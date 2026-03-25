"""
Парсер Word-файлов с тестовыми вопросами.

Поддерживаемый формат:
─────────────────────────────────────────────────
1. Текст первого вопроса?
А) Первый вариант
*Б) Правильный ответ      ← звёздочка = правильный ответ
В) Третий вариант
Г) Четвёртый вариант

2. Текст второго вопроса?
*A) The right answer
B) Wrong
C) Wrong
D) Wrong
─────────────────────────────────────────────────
• Номер вопроса: цифра + точка или скобка  (1. / 1)
• Вариант: одна буква (А-Д, A-E) + ) или .  (А) / А. / A) / A.)
• Звёздочка (*) перед буквой варианта — правильный ответ
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

# Вариант:  "*А)" / "А)" / "*A." / "A."  — с опциональной звёздочкой
_OPT_RE = re.compile(
    r'^\s*(?P<star>\*)?(?P<letter>[АБВГДЕЖЗИKABCDEFGHabcdefghАБВГДЕЖЗИK])[).]\s*(?P<text>.+)',
    re.DOTALL,
)


def parse_docx(file_bytes: bytes) -> list[ParsedQuestion]:
    """Принимает байты .docx файла, возвращает список вопросов."""
    from docx import Document
    import io

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    questions: list[ParsedQuestion] = []
    current_q: ParsedQuestion | None = None

    for para in paragraphs:
        q_match = _Q_RE.match(para)
        opt_match = _OPT_RE.match(para)

        if q_match:
            if current_q is not None:
                questions.append(current_q)
            current_q = ParsedQuestion(text=q_match.group(1).strip())

        elif opt_match and current_q is not None:
            current_q.options.append(ParsedOption(
                text=opt_match.group('text').strip(),
                is_correct=opt_match.group('star') is not None,
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
