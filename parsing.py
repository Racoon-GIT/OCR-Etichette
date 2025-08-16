import re

RE_MODEL = re.compile(r"\b(STAN\s*SMITH|CAMPUS\s*00s|GAZELLE|SAMBA|FORUM|SUPERSTAR)\b", re.IGNORECASE)
RE_ARTICOLO = re.compile(r"\b[A-Z]{1,2}\d{4,6}\b")  # M20325, IF8774, HQ4327...
RE_COLORE = re.compile(r"\b[A-Z0-9]{3,}(?:/[A-Z0-9]{3,}){1,3}\b")
RE_TAGLIA_FR = re.compile(r"\b(3[0-9]|4[0-6])(?:[½⅓⅔]| ?1/2| ?1/3| ?2/3)?\b")
RE_BARCODE_13 = re.compile(r"\b\d{13}\b")
RE_BARCODE_SPACED = re.compile(r"(?:\d\s*){13,}")

def normalize_fraction(s: str) -> str:
    return (s.replace("½", " 1/2")
             .replace("⅓", " 1/3")
             .replace("⅔", " 2/3"))

def parse_fields(text_general: str, text_digits: str):
    t = normalize_fraction(" ".join(text_general.split()))
    d = " ".join(text_digits.split())

    model = (RE_MODEL.search(t).group(1).upper() if RE_MODEL.search(t) else "")
    articoli = RE_ARTICOLO.findall(t)
    articolo = articoli[0] if articoli else ""

    colore = ""
    if articolo:
        idx = t.find(articolo)
        if idx != -1:
            m = RE_COLORE.search(t[idx: idx+100])
            if m: colore = m.group(0)
    if not colore:
        m = RE_COLORE.search(t)
        if m: colore = m.group(0)

    size = ""
    m = RE_TAGLIA_FR.search(t)
    if m: size = m.group(0)

    barcode = ""
    m = RE_BARCODE_13.search(d)
    if m: barcode = m.group(0)
    if not barcode:
        m = RE_BARCODE_SPACED.search(d) or RE_BARCODE_SPACED.search(t)
        if m:
            digits = re.sub(r"\D", "", m.group(0))
            if len(digits) == 13:
                barcode = digits

    score = 0
    score += 25 if model else 0
    score += 25 if articolo else 0
    score += 25 if colore else 0
    score += 25 if barcode else 0
    stato = "OK" if score >= 75 else "REVIEW"
    return model, articolo, colore, size, barcode, score, stato
