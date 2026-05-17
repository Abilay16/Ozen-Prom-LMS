"""
Utilities for comparing full names from different sources
(system DB vs NUC RK EDS certificate CN).

Problem: NUC RK certificates for юр.лица may encode names without
Kazakh-specific Unicode letters (Ұ→У, Қ→К, Ғ→Г, Ң→Н, Ү→У, Ә→А, І→И, Ө→О)
and in ALL CAPS, while the system stores names in proper case with full Unicode.

normalize_name() makes both sides comparable:
  "АЯПБЕРГЕНОВ АЛПАМЫС АСКАРУЛЫ"  →  "аскарулы алпамыс аяпбергенов"
  "Аяпбергенов Алпамыс Аскарұлы"  →  "аскарулы алпамыс аяпбергенов"
  → match ✓
"""
import re

# Mapping Kazakh-specific Cyrillic letters → closest base Cyrillic
# Used to bridge the gap between NUC cert encoding and system storage
_KAZAKH_MAP: dict[str, str] = {
    "қ": "к",
    "ұ": "у",
    "ү": "у",
    "ғ": "г",
    "ң": "н",
    "ә": "а",
    "і": "и",
    "ө": "о",
    "ё": "е",
}


def normalize_name(name: str) -> str:
    """
    Return a canonical representation of a person's full name for loose comparison.

    Steps:
      1. Lowercase
      2. Map Kazakh-specific letters to base Cyrillic equivalents
      3. Collapse whitespace
      4. Split into tokens and sort (order-insensitive: Фамилия Имя Отчество
         vs Имя Отчество Фамилия — treated the same)

    Returns sorted tokens joined by single space.
    """
    s = name.lower().strip()
    for src, dst in _KAZAKH_MAP.items():
        s = s.replace(src, dst)
    tokens = sorted(re.split(r"\s+", s))
    return " ".join(tokens)


def names_match(cert_name: str, system_name: str) -> bool:
    """Return True if the certificate name matches the system full name.

    Handles two cases:
    - Certificate contains full FIO (3 tokens): exact set match.
    - Certificate contains only Фамилия + Имя (2 tokens, no patronymic):
      both tokens must be present in the system name tokens.

    Minimum 2 tokens in the certificate are required to avoid false positives
    from a single-token (surname-only) certificate.
    """
    cert_tokens = set(re.split(r"\s+", normalize_name(cert_name)))
    sys_tokens = set(re.split(r"\s+", normalize_name(system_name)))
    if len(cert_tokens) < 2:
        return False
    return cert_tokens <= sys_tokens
