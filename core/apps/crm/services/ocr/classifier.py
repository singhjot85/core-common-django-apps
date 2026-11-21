"""
Document classification heuristics for Indian KYC and vehicle certificates.
"""

_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "aadhaar": [
        ("unique identification authority of india", 5),
        ("uidai", 4),
        ("aadhaar", 4),
        ("मेरा आधार मेरी पहचान", 5),
        ("government of india", 1),
    ],
    "driving_license": [
        ("driving licence", 5),
        ("driving license", 5),
        ("form 7", 3),
        ("union of india driving licence", 5),
        ("licence to drive", 4),
        ("dl no", 3),
    ],
    "puc": [
        ("pollution under control certificate", 5),
        ("puc certificate", 4),
        ("pucc", 4),
        ("emission test", 3),
    ],
    "insurance": [
        ("certificate of insurance", 5),
        ("policy schedule", 4),
        ("motor insurance", 4),
        ("package policy", 3),
        ("liability only policy", 3),
    ],
    "registration_certificate": [
        ("certificate of registration", 5),
        ("form 23", 4),
        ("registration certificate", 4),
        ("chassis no", 2),
        ("engine no", 2),
    ],
}


def classify(text: str) -> str:
    """
    Score keyword presence across document text to classify document type.

    Args:
        text (str): Document text block.

    Returns:
        str: Detected document type identifier or 'unknown'.
    """
    lowered = text.lower()
    scores: dict[str, int] = {k: 0 for k in _KEYWORDS}
    for doc_type, terms in _KEYWORDS.items():
        for term, weight in terms:
            if term in lowered:
                scores[doc_type] += weight

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"
