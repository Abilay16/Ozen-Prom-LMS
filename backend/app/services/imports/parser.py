"""
Import parser service.
Reads an Excel file, detects the header row and columns by header names,
and returns a preview of rows with status.

Что учитывается (всё встречалось в реальных файлах):
- над таблицей бывает заголовок («Список сотрудников ТОО …») — строку
  с заголовками колонок ищем среди первых строк, а не берём первую;
- ФИО бывает одной колонкой или тремя: «Фамилия», «Имя», «Отчество»;
- короткие заголовки («№», «П») не должны совпадать с частью слова
  («предприятие») — заголовок сравнивается целиком или по вхождению
  известного названия в заголовок, но не наоборот;
- пустые строки (оформление, итоги) пропускаются, а не становятся ошибками.
"""
import re
import pandas as pd


# Возможные названия колонок (после нормализации: нижний регистр, без знаков препинания)
COLUMN_ALIASES = {
    "full_name": ["фио", "ф и о", "фамилия имя отчество", "фамилия и имя", "сотрудник", "работник"],
    "position": ["должность", "профессия", "специальность"],
    "organization": ["организация", "предприятие", "компания", "работодатель", "место работы"],
    "disciplines": ["дисциплина", "предмет", "вид обучения", "программа"],
}
# Раздельные колонки ФИО
NAME_PARTS = {"last": ["фамилия"], "first": ["имя"], "middle": ["отчество"]}

HEADER_SCAN_ROWS = 15


def _normalize_header(h) -> str:
    text = str(h).strip().lower().replace("ё", "е")
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _matches(header: str, alias: str) -> bool:
    if not header:
        return False
    return header == alias or re.search(rf"(^|\s){re.escape(alias)}(\s|$)", header) is not None


def _find(headers: list[str], aliases: list[str], exact: bool = False) -> int | None:
    for i, h in enumerate(headers):
        for alias in aliases:
            if (h == alias) if exact else _matches(h, alias):
                return i
    return None


def _detect_columns(headers: list) -> dict[str, int]:
    """Map logical field name → column index."""
    norm = [_normalize_header(h) for h in headers]
    mapping: dict[str, int] = {}
    for field, aliases in COLUMN_ALIASES.items():
        idx = _find(norm, aliases)
        if idx is not None and idx not in mapping.values():
            mapping[field] = idx
    if "full_name" not in mapping:
        last = _find(norm, NAME_PARTS["last"], exact=True)
        first = _find(norm, NAME_PARTS["first"], exact=True)
        if last is not None and first is not None:
            mapping["name_last"] = last
            mapping["name_first"] = first
            middle = _find(norm, NAME_PARTS["middle"], exact=True)
            if middle is not None:
                mapping["name_middle"] = middle
    return mapping


def _has_name_column(mapping: dict) -> bool:
    return "full_name" in mapping or "name_last" in mapping


def _cell(values: list, mapping: dict, field: str) -> str:
    idx = mapping.get(field)
    if idx is None or idx >= len(values):
        return ""
    return " ".join(str(values[idx]).split())


class ImportParserService:
    def parse_preview(self, file_path: str) -> dict:
        try:
            raw = pd.read_excel(file_path, dtype=str, header=None)
        except Exception as e:
            return {"parse_error": f"Не удалось прочитать Excel-файл: {e}", "rows": [], "column_mapping": {}}

        raw = raw.fillna("")
        grid = raw.values.tolist()

        # Строка заголовков — первая, где нашлась колонка ФИО.
        header_idx, col_map = 0, {}
        for i, row in enumerate(grid[:HEADER_SCAN_ROWS]):
            mapping = _detect_columns(row)
            if _has_name_column(mapping):
                header_idx, col_map = i, mapping
                break
        headers = [str(h).strip() or f"Колонка {j + 1}" for j, h in enumerate(grid[header_idx])] if grid else []

        rows = []
        for i, values in enumerate(grid[header_idx + 1:], start=header_idx + 2):
            if all(not str(v).strip() for v in values):
                continue  # пустая строка оформления

            if "full_name" in col_map:
                full_name = _cell(values, col_map, "full_name")
            else:
                full_name = " ".join(filter(None, (
                    _cell(values, col_map, "name_last"),
                    _cell(values, col_map, "name_first"),
                    _cell(values, col_map, "name_middle"),
                )))

            parsed = {
                "row_number": i,  # номер строки в Excel (1-based)
                "raw": {headers[j] if j < len(headers) else f"Колонка {j + 1}": str(v) for j, v in enumerate(values)},
                "full_name": full_name,
                "position": _cell(values, col_map, "position"),
                "organization": _cell(values, col_map, "organization"),
                "disciplines_raw": _cell(values, col_map, "disciplines"),
                "status": "ok",
                "warnings": [],
            }

            if not parsed["full_name"]:
                parsed["status"] = "error"
                parsed["warnings"].append("ФИО не заполнено")
            if not parsed["position"]:
                parsed["warnings"].append("Должность не указана")
                if parsed["status"] == "ok":
                    parsed["status"] = "manual_review"

            rows.append(parsed)

        summary = {
            "total": len(rows),
            "ok": sum(1 for r in rows if r["status"] == "ok"),
            "manual_review": sum(1 for r in rows if r["status"] == "manual_review"),
            "error": sum(1 for r in rows if r["status"] == "error"),
            "detected_columns": col_map,
            "header_row": header_idx + 1,
            "headers": headers,
            "rows": rows,
        }
        if not _has_name_column(col_map):
            summary["parse_error"] = (
                "Не найдена колонка с ФИО. Нужна колонка «ФИО» (или «Фамилия» и «Имя») "
                "в одной из первых строк таблицы."
            )
        return summary
