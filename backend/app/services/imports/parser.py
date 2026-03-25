"""
Import parser service.
Reads an Excel file, detects columns by fuzzy header matching,
and returns a preview of rows with status.
"""
import re
from typing import Any
import pandas as pd


# Possible column name variants for each field (lowercase, stripped)
COLUMN_ALIASES = {
    "full_name": ["фио", "ф.и.о", "ф.и.о.", "имя", "сотрудник", "работник", "фамилия имя отчество"],
    "position":  ["должность", "профессия", "специальность", "должность/профессия"],
    "organization": ["организация", "предприятие", "компания", "работодатель"],
    "disciplines": ["дисциплина", "предмет", "обучение", "вид обучения", "программа"],
}


def _normalize_header(h: str) -> str:
    return re.sub(r"\s+", " ", str(h).strip().lower())


def _detect_columns(headers: list[str]) -> dict[str, int]:
    """Map logical field name → column index."""
    mapping = {}
    norm_headers = [_normalize_header(h) for h in headers]
    for field, aliases in COLUMN_ALIASES.items():
        for i, h in enumerate(norm_headers):
            if any(alias in h or h in alias for alias in aliases):
                mapping[field] = i
                break
    return mapping


class ImportParserService:
    def parse_preview(self, file_path: str) -> dict:
        try:
            df = pd.read_excel(file_path, dtype=str)
        except Exception as e:
            return {"error": str(e), "rows": [], "column_mapping": {}}

        df = df.fillna("")
        headers = list(df.columns)
        col_map = _detect_columns(headers)

        rows = []
        for idx, row in df.iterrows():
            values = list(row)
            parsed = {
                "row_number": int(idx) + 2,  # +2 for 1-based + header row
                "raw": dict(zip(headers, values)),
                "full_name": values[col_map["full_name"]].strip() if "full_name" in col_map else "",
                "position": values[col_map["position"]].strip() if "position" in col_map else "",
                "organization": values[col_map["organization"]].strip() if "organization" in col_map else "",
                "disciplines_raw": values[col_map["disciplines"]].strip() if "disciplines" in col_map else "",
                "status": "ok",
                "warnings": [],
            }

            # Basic validation
            if not parsed["full_name"]:
                parsed["status"] = "error"
                parsed["warnings"].append("ФИО не заполнено")
            if not parsed["position"]:
                parsed["warnings"].append("Должность не указана")
                if parsed["status"] == "ok":
                    parsed["status"] = "manual_review"
            if not parsed["disciplines_raw"]:
                parsed["warnings"].append("Дисциплина не указана")
                if parsed["status"] == "ok":
                    parsed["status"] = "manual_review"

            rows.append(parsed)

        summary = {
            "total": len(rows),
            "ok": sum(1 for r in rows if r["status"] == "ok"),
            "manual_review": sum(1 for r in rows if r["status"] == "manual_review"),
            "error": sum(1 for r in rows if r["status"] == "error"),
            "detected_columns": col_map,
            "headers": headers,
            "rows": rows,
        }
        return summary
