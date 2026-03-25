"""
Position normalizer service.
Strips punctuation, lowercases, removes extra spaces.
"""
import re


def normalize_position(raw: str) -> str:
    if not raw:
        return ""
    text = raw.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)  # replace punctuation with space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def positions_match(keyword: str, normalized_position: str) -> bool:
    """Check if a rule keyword is contained in the normalized position string."""
    kw = normalize_position(keyword)
    return kw in normalized_position
