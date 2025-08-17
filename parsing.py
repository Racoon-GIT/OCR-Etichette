# parsing.py
import re

# ── Pattern base ───────────────────────────────────────────────────────────────

# Base models (estendibile)
_BASE_MODELS = r"(?:STAN\s*SMITH|SAMBA|GAZELLE|SUPERSTAR|CAMPUS|FORUM)"

# Feature tokens (fino a 2): 00s/OG/II/2/ADV/BOLD/INDOOR/MID/LOW/HI/CL
_FEATURE_TOK = r"(?:00S|00s|OG|II|2|ADV|BOLD|INDOOR|MID|LOW|HI|CL)"

# Target tokens (max 1): J/K/C/W/M/EL/CF
_TARGET_TOK  = r"(?:J|K|C|W|M|EL|CF)"

# Modello = base + (feature){0,2} + (target)?
RE_MODEL = re.compile(
    rf"\b({_BASE_MODELS}(?:\s+{_FEATURE_TOK}){{0,2}}(?:\s+{_TARGET_TOK})?)\b",
    re.IGNORECASE,
)

# Codice articolo (es. IE3675, M20325, HQ4327…)
RE_ARTICOLO = re.compile(r"\b[A-Z]{1,2}\d{4,6}\b")

# Colore: 2–4 token alfanumerici ≥3 char separati da “/” (include numeri tipo GUM5)
RE_COLORE = re.compile(r"\b[A-Z0-9]{3,}(?:/[A-Z0-9]{3,}){1,3}\b")

# Taglia FR plausibile con frazioni
RE_TAGLIA_FR = re.compile(r"\b(3[0-9]|4[0-6])(?:[½⅓⅔]| ?1/2| ?1/3| ?2/3)?\b")

# Barcode EAN-13 (pulito o “spaziato”)
RE_BARCODE_13 = re.compile(r"\b\d{13}\b")
RE_BARCODE_SPACED = re.compile(r"(?:\d\D*){13,16}")

# ── Utility ────────────────────────────────────────────────────────────────────

def normalize_fraction(s: str) -> str:
    return (
        s.replace("½", " 1/2")
         .replace("⅓", " 1/3")
         .replace("⅔", " 2/3")
         .replace("’", "'")
    )

def _fix_common_ocr(text: str) -> str:
    t = text
    # 0/O confusione su CAMPUS 00s
    t = re.sub(r"\bCAMPUS\s*OOS\b", "CAMPUS 00s", t, flags=re.IGNORECASE)
    t = re.sub(r"\bCAMPUS\s*0OS\b", "CAMPUS 00s", t, flags=re.IGNORECASE)
    t = re.sub(r"\bCAMPUS\s*O0S\b", "CAMPUS 00s", t, flags=re.IGNORECASE)
    t = re.sub(r"\bCAMPUS\s*0+S\b", "CAMPUS 00s", t, flags=re.IGNORECASE)
    # GUMS (S↔5) → GUM5
    t = re.sub(r"\bGUMS\b", "GUM5", t, flags=re.IGNORECASE)
    return t

def extract_fr_size(text: str) -> str:
    """Preferisce la cella 'F' (FR); fallback a pattern generico."""
    t = normalize_fraction(text)
    m = re.search(r"\bF\b[^0-9]*(\d{2}(?: ?(?:1/2|1/3|2/3)|[½⅓⅔])?)", t, re.IGNORECASE)
    if m:
        s = m.group(1)
        return normalize_fraction(s).strip()
    m = RE_TAGLIA_FR.search(t)
    return normalize_fraction(m.group(0)) if m else ""

def _normalize_model(raw: str) -> str:
    """Normalizza modello: spazi, 00s, II, ordine base+feature+target."""
    if not raw:
        return ""
    t = re.sub(r"\s+", " ", raw.upper()).strip()

    parts = t.split(" ")
    base = []
    features = []
    target = []

    i = 0
    if i < len(parts) and parts[i] in {"STAN", "SAMBA", "GAZELLE", "SUPERSTAR", "CAMPUS", "FORUM"}:
        if parts[i] == "STAN" and i + 1 < len(parts) and parts[i+1] == "SMITH":
            base = ["STAN", "SMITH"]; i += 2
        else:
            base = [parts[i]]; i += 1

    while i < len(parts):
        p = parts[i]
        if p in {"J","K","C","W","M","EL","CF"} and not target:
            target = [p]; i += 1; continue
        if p in {"00S","00s","OG","II","2","ADV","BOLD","INDOOR","MID","LOW","HI","CL"} and len(features) < 2:
            features.append(p); i += 1; continue
        i += 1  # ignora token non riconosciuti

    # 00S -> 00s; 2 -> II
    features = ["00s" if f in {"00S","00s"} else ("II" if f == "2" else f) for f in features]

    out = " ".join(base + features + target).strip()
    out = re.sub(r"\bCAMPUS 00S\b", "CAMPUS 00s", out)
    out = re.sub(r"( \b\w+\b)( \1\b)+", r"\1", out)  # no duplicati consecutivi
    return out

# ── Parser principale ──────────────────────────────────────────────────────────

def parse_fields(text_general: str, text_digits: str):
    """
    Ritorna: (model, articolo, colore, size_fr, barcode, score, stato)
    score in 0..100; stato OK se >= 75.
    """
    t = _fix_common_ocr(normalize_fraction(" ".join(text_general.split())))
    d = " ".join(text_digits.split())

    # Modello
    model = ""
    mm = RE_MODEL.search(t)
    if mm:
        model = _normalize_model(mm.group(0))

    # Articolo
    articolo = ""
    am = RE_ARTICOLO.search(t)
    if am:
        articolo = am.group(0)

    # Colore (prova vicino all’articolo, poi globale)
    colore = ""
    if articolo:
        idx = t.find(articolo)
        window = t[idx: idx + 150] if idx != -1 else t
        cm = RE_COLORE.search(window)
        if cm:
            colore = cm.group(0)
    if not colore:
        cm = RE_COLORE.search(t)
        if cm:
            colore = cm.group(0)
    if colore.upper().endswith("GUMS"):
        colore = colore[:-1] + "5"

    # Taglia FR
    size = extract_fr_size(t)

    # Barcode
    barcode = ""
    bm = RE_BARCODE_13.search(d)
    if bm:
        barcode = bm.group(0)
    if not barcode:
        bm = RE_BARCODE_SPACED.search(d) or RE_BARCODE_SPACED.search(t)
        if bm:
            digits = re.sub(r"\D", "", bm.group(0))
            if len(digits) >= 13:
                barcode = digits[:13]

    # Scoring
    score = 0
    score += 25 if model else 0
    score += 25 if articolo else 0
    score += 25 if colore else 0
    score += 25 if barcode else 0
    stato = "OK" if score >= 75 else "REVIEW"

    return model.strip(), articolo, colore, size, barcode, score, stato
