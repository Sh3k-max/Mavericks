import re
from typing import Dict, Any, Optional
from ..utils.logger import logger
from .tag_extractor import TagExtractor, KNOWN_PREFIXES

class TagNormalizer:
    """
    Normalizes extracted P&ID tags:
    - Resolves contextual OCR typos (0/O, 1/I, 5/S, 8/B).
    - Cleans dashes, en-dashes, em-dashes, underscores, and extra spaces.
    - Standardizes into standard format: PREFIX-NUMBER[SUFFIX] or UNIT-PREFIX-NUMBER[SUFFIX].
    """

    def __init__(self):
        self.extractor = TagExtractor()

        # Common letter typos in prefixes
        self.prefix_corrections = {
            "P0": "PO",
            "5V": "SV",
            "1V": "IV",
            "8V": "BV",
        }

    def normalize_tag(self, text: str) -> Optional[Dict[str, Any]]:
        parsed = self.extractor.parse_tag(text)
        if not parsed:
            return None

        raw_prefix = parsed["prefix"]
        raw_number = parsed["number"]
        raw_suffix = parsed["suffix"]
        raw_unit = parsed["unit"]

        # 1. Normalize prefix (letters only context)
        normalized_prefix = raw_prefix.upper()
        # Contextual correction: if prefix has digits like 0 or 1 or 5 or 8
        prefix_digit_to_letter = {'0': 'O', '1': 'I', '5': 'S', '8': 'B'}
        fixed_prefix_chars = []
        for char in normalized_prefix:
            fixed_prefix_chars.append(prefix_digit_to_letter.get(char, char))
        normalized_prefix = "".join(fixed_prefix_chars)

        # 2. Normalize number (digits only context)
        normalized_number_chars = []
        letter_to_digit = {
            'O': '0', 'o': '0',
            'I': '1', 'i': '1', 'l': '1', '|': '1',
            'S': '5', 's': '5',
            'B': '8', 'b': '8',
            'Z': '2', 'z': '2'
        }
        for char in raw_number:
            normalized_number_chars.append(letter_to_digit.get(char, char))
        normalized_number = "".join(normalized_number_chars)

        # 3. Normalize suffix (letter context)
        normalized_suffix = raw_suffix.upper()
        if normalized_suffix in prefix_digit_to_letter:
            normalized_suffix = prefix_digit_to_letter[normalized_suffix]

        # 4. Assemble canonical tag representation: e.g. PT-101, FCV-201, 10-P-301A
        prefix_part = normalized_prefix
        if raw_unit:
            canonical_tag = f"{raw_unit}-{prefix_part}-{normalized_number}{normalized_suffix}"
        else:
            canonical_tag = f"{prefix_part}-{normalized_number}{normalized_suffix}"

        return {
            "canonical_tag": canonical_tag,
            "prefix": normalized_prefix,
            "number": normalized_number,
            "suffix": normalized_suffix,
            "unit": raw_unit,
            "is_known_prefix": normalized_prefix in KNOWN_PREFIXES,
            "original_text": text
        }
