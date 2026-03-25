"""
Custom transliteration for Kazakh + Russian names.
Standard libraries (unidecode, transliterate) don't cover Kazakh-specific chars.
"""

KAZ_TRANSLIT = {
    'ә': 'a',  'Ә': 'A',
    'ғ': 'gh', 'Ғ': 'Gh',
    'қ': 'q',  'Қ': 'Q',
    'ң': 'ng', 'Ң': 'Ng',
    'ө': 'o',  'Ө': 'O',
    'ұ': 'u',  'Ұ': 'U',
    'ү': 'u',  'Ү': 'U',
    'һ': 'h',  'Һ': 'H',
    'і': 'i',  'І': 'I',
}

RU_TRANSLIT = {
    'а': 'a',  'А': 'A',
    'б': 'b',  'Б': 'B',
    'в': 'v',  'В': 'V',
    'г': 'g',  'Г': 'G',
    'д': 'd',  'Д': 'D',
    'е': 'e',  'Е': 'E',
    'ё': 'yo', 'Ё': 'Yo',
    'ж': 'zh', 'Ж': 'Zh',
    'з': 'z',  'З': 'Z',
    'и': 'i',  'И': 'I',
    'й': 'y',  'Й': 'Y',
    'к': 'k',  'К': 'K',
    'л': 'l',  'Л': 'L',
    'м': 'm',  'М': 'M',
    'н': 'n',  'Н': 'N',
    'о': 'o',  'О': 'O',
    'п': 'p',  'П': 'P',
    'р': 'r',  'Р': 'R',
    'с': 's',  'С': 'S',
    'т': 't',  'Т': 'T',
    'у': 'u',  'У': 'U',
    'ф': 'f',  'Ф': 'F',
    'х': 'kh', 'Х': 'Kh',
    'ц': 'ts', 'Ц': 'Ts',
    'ч': 'ch', 'Ч': 'Ch',
    'ш': 'sh', 'Ш': 'Sh',
    'щ': 'sch','Щ': 'Sch',
    'ъ': '',   'Ъ': '',
    'ы': 'y',  'Ы': 'Y',
    'ь': '',   'Ь': '',
    'э': 'e',  'Э': 'E',
    'ю': 'yu', 'Ю': 'Yu',
    'я': 'ya', 'Я': 'Ya',
}

FULL_TABLE = {**KAZ_TRANSLIT, **RU_TRANSLIT}


def transliterate(text: str) -> str:
    """Convert Kazakh/Russian text to Latin."""
    result = []
    for char in text:
        result.append(FULL_TABLE.get(char, char))
    return "".join(result)


def transliterate_name_to_login(full_name: str) -> str:
    """
    Convert full name to login base.
    Input: "Алиев Абылай Илиясулы"
    Output: "AliyevAI"
    """
    parts = full_name.strip().split()
    if not parts:
        return "user"

    surname = transliterate(parts[0])
    initials = "".join(transliterate(p[0]).upper() for p in parts[1:] if p)

    # Clean non-alphanumeric
    surname = "".join(c for c in surname if c.isalpha())
    initials = "".join(c for c in initials if c.isalpha())

    return f"{surname}{initials}"
