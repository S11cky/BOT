# --- target (cieľová firma) extrakcia ---
TARGET_PATTERNS = [
    r"\b(?:acquires?|acquired|buy(?:s|ing)?|purchases?|to acquire|kupuje|akvíruje)\s+([A-Z][\w&.\- ]{2,140})",
    r"\b(?:acquisition|akvizíci[ae]|akvizícia)\s+of\s+([A-Z][\w&.\- ]{2,140})\s+by\s+[A-Z][\w&.\- ]{2,140}",
    r"\b([A-Z][\w&.\- ]{2,140})\s+(?:to be\s+)?(?:acquired|bought)\s+by\s+[A-Z][\w&.\- ]{2,140}",
    r"\b(?:to acquire|plánuje kúpiť|mieni kúpiť)\s+([A-Z][\w&.\- ]{2,140})",
    r"\b(?:kupuje|akvíruje)\s+(?:spoločnosť|firmu)?\s*([A-Z][\w&.\- ]{2,140})"
]

def clean_target(t: str, acquirer: str | None) -> str | None:
    if not t:
        return None
    t = re.sub(r"\s+(?:for|za|worth|deal|transaction|suma|sumou)\b.*$", "", t, flags=re.I)
    t = t.strip(" \"'•-–—.,")
    if acquirer and fuzz.partial_ratio(t.lower(), acquirer.lower()) > 90:
        return None
    if len(t.split()) == 1 and t.lower() in {"company","spoločnosť","firmu","target"}:
        return None
    return t if t else None

def extract_target(acquirer: str | None, text: str) -> str | None:
    for pat in TARGET_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            cand = m.group(1)
            ct = clean_target(cand, acquirer)
            if ct:
                return ct
    return None
