"""
Парсер Word-файлов с тестовыми вопросами.

Поддерживаемые форматы правильного ответа:
─────────────────────────────────────────────────
1. Звёздочка ПЕРЕД буквой:    *А) Правильный ответ
2. Звёздочка ПОСЛЕ скобки:    А)* Правильный ответ
3. Звёздочка перед текстом:   А) *Правильный ответ
4. Жирный шрифт (bold) на всём варианте или на букве
5. Звёздочка в конце текста:  А) Правильный ответ*
─────────────────────────────────────────────────
• Номер вопроса: цифра + точка или скобка  (1. / 1)
• Вариант: одна буква (А-Д, A-E) + ) или .  (А) / А. / A) / A.)
• Пустые строки между вопросами — допустимы
• Порядок вопросов и вариантов сохраняется
"""

import re
from dataclasses import dataclass, field


@dataclass
class ParsedOption:
    text: str
    is_correct: bool


@dataclass
class ParsedQuestion:
    text: str
    options: list[ParsedOption] = field(default_factory=list)


# ─── Regex ────────────────────────────────────────────────────────────────────

# Номер вопроса:  "1." / "1)" / "01."
_Q_RE = re.compile(r'^\s*\d+[.)]\s+(.+)', re.DOTALL)

# Вариант — поддерживает * до и после скобки, и до текста:
#   *А) текст  |  А)* текст  |  А) *текст  |  А) текст
_LETTERS = r'[АБВГДЕЖЗИКABCDEFGHabcdefghАБВГДЕЖЗИК]'
_OPT_RE = re.compile(
    r'^\s*(?P<star1>\*)?(?P<letter>' + _LETTERS + r')[).]\s*(?P<star2>\*)?(?P<text>.+)',
    re.DOTALL,
)


def _para_is_bold(para) -> bool:
    """Возвращает True если весь параграф (или первый ран с буквой варианта) жирный."""
    runs = [r for r in para.runs if r.text.strip()]
    if not runs:
        return False
    # Считаем жирным если первый непустой ран жирный
    return bool(runs[0].bold)


def parse_docx(file_bytes: bytes) -> list[ParsedQuestion]:
    """Принимает байты .docx файла, возвращает список вопросов."""
    from docx import Document
    import io

    doc = Document(io.BytesIO(file_bytes))

    questions: list[ParsedQuestion] = []
    current_q: ParsedQuestion | None = None

    for para in doc.paragraphs:
        raw = para.text.strip()
        if not raw:
            continue

        q_match = _Q_RE.match(raw)
        opt_match = _OPT_RE.match(raw)

        if q_match:
            if current_q is not None:
                questions.append(current_q)
            current_q = ParsedQuestion(text=q_match.group(1).strip())

        elif opt_match and current_q is not None:
            star1 = opt_match.group('star1')  # * before letter
            star2 = opt_match.group('star2')  # * after bracket
            text_part = opt_match.group('text').strip()

            # * at start of answer text: "А) *текст"
            star3 = text_part.startswith('*')
            if star3:
                text_part = text_part[1:].strip()

            # * at end of answer text: "А) текст*"
            star4 = text_part.endswith('*')
            if star4:
                text_part = text_part[:-1].strip()

            is_correct = bool(star1 or star2 or star3 or star4 or _para_is_bold(para))

            current_q.options.append(ParsedOption(
                text=text_part,
                is_correct=is_correct,
            ))

    if current_q is not None:
        questions.append(current_q)

    return questions


def validate_parsed(questions: list[ParsedQuestion]) -> list[str]:
    """Возвращает список предупреждений (если вопросы корректны — пустой список)."""
    warnings: list[str] = []
    if not questions:
        warnings.append("Не найдено ни одного вопроса. Проверьте формат файла.")
        return warnings

    for i, q in enumerate(questions, 1):
        if not q.options:
            warnings.append(f"Вопрос {i}: нет вариантов ответов.")
        elif not any(o.is_correct for o in q.options):
            warnings.append(f"Вопрос {i}: не отмечен правильный ответ (используйте * перед буквой).")

    return warnings
