import pytest
from backend.app.services.tag_normalizer import TagNormalizer
from backend.app.services.tag_extractor import TagExtractor

def test_tag_extractor_patterns():
    extractor = TagExtractor()
    
    assert extractor.is_likely_tag("PT-101")
    assert extractor.is_likely_tag("FCV-201")
    assert extractor.is_likely_tag("P-301A")
    assert extractor.is_likely_tag("TT 201")
    assert extractor.is_likely_tag("FT101")
    
    # Non-tags
    assert not extractor.is_likely_tag("REV")
    assert not extractor.is_likely_tag("SHEET")
    assert not extractor.is_likely_tag("DRAWING")

def test_tag_normalizer_typo_correction():
    normalizer = TagNormalizer()

    # Standard clean tags
    res1 = normalizer.normalize_tag("PT-101")
    assert res1["canonical_tag"] == "PT-101"
    assert res1["prefix"] == "PT"
    assert res1["number"] == "101"

    # Letter 'O' instead of digit '0' in number
    res2 = normalizer.normalize_tag("PT-1O1")
    assert res2["canonical_tag"] == "PT-101"
    assert res2["number"] == "101"

    # Letter 'I' instead of digit '1' in number
    res3 = normalizer.normalize_tag("TT-I02")
    assert res3["canonical_tag"] == "TT-102"
    assert res3["number"] == "102"

    # Letter 'S' instead of digit '5' in number
    res4 = normalizer.normalize_tag("FCV-20S")
    assert res4["canonical_tag"] == "FCV-205"

    # Space separated or no dash
    res5 = normalizer.normalize_tag("FT 301")
    assert res5["canonical_tag"] == "FT-301"

    res6 = normalizer.normalize_tag("P301")
    assert res6["canonical_tag"] == "P-301"

    # Suffix preserved
    res7 = normalizer.normalize_tag("P-101A")
    assert res7["canonical_tag"] == "P-101A"
    assert res7["suffix"] == "A"
