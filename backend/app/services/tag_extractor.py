import re
from typing import Dict, Any, Optional, Tuple, List
from ..utils.logger import logger

# Standard ISA-5.1 P&ID instrumentation and equipment prefixes
KNOWN_PREFIXES = {
    # Transmitters & Indicators
    "PT", "PI", "PIC", "PIT", "PDT", "PDI",
    "TT", "TI", "TIC", "TIT", "TE",
    "FT", "FI", "FIC", "FIT", "FE",
    "LT", "LI", "LIC", "LIT", "LG",
    "AT", "AI", "AIC",
    # Valves
    "FCV", "PCV", "TCV", "LCV", "PSV", "PRV", "XV", "HV", "MOV", "SOV", "BDV", "LV", "PV", "TV", "FV",
    # Equipment
    "P", "PU", "PUMP", "TK", "T", "V", "E", "C", "CMP", "K", "M", "R", "D", "F",
    # Off-page Connectors / Flow Indicators
    "CONN", "OPC"
}

class TagExtractor:
    """
    Extracts P&ID tags from text tokens and parses them into:
    - prefix
    - number
    - suffix
    """

    # Matches tags like PT-101, FCV-201, P-301A, PT 101, PT101, 10-PT-101, etc.
    TAG_REGEX = re.compile(
        r"(?:(?P<unit>\d{1,3})-)?(?P<prefix>[A-Za-z]{1,5})[\s\-_]*(?P<number>[0-9OISB]{2,6})(?P<suffix>[A-Za-z])?",
        re.IGNORECASE
    )

    def is_likely_tag(self, text: str) -> bool:
        cleaned = text.strip()
        if len(cleaned) < 2 or len(cleaned) > 25:
            return False
        
        # Avoid common drawing title block words
        ignored_words = {"REV", "SHEET", "SCALE", "DATE", "DRAWING", "APPROVED", "CHECKED", "PROJECT", "CLIENT", "DWG", "NOTE", "NOTES"}
        if cleaned.upper() in ignored_words:
            return False

        match = self.TAG_REGEX.search(cleaned)
        if match:
            prefix = match.group("prefix").upper()
            if prefix in KNOWN_PREFIXES or len(prefix) <= 4:
                return True
        return False

    def parse_tag(self, text: str) -> Optional[Dict[str, Any]]:
        cleaned = text.strip()
        match = self.TAG_REGEX.search(cleaned)
        if not match:
            return None

        unit = match.group("unit") or ""
        prefix = match.group("prefix").upper()
        number = match.group("number")
        suffix = (match.group("suffix") or "").upper()

        return {
            "raw_text": text,
            "unit": unit,
            "prefix": prefix,
            "number": number,
            "suffix": suffix,
            "is_known_prefix": prefix in KNOWN_PREFIXES
        }
