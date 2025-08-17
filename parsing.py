# ── Modello: base + (feature)* + (target)? ─────────────────────────────────────
# Base models supportati (puoi estendere facilmente la lista)
_BASE_MODELS = r"(?:STAN\s*SMITH|SAMBA|GAZELLE|SUPERSTAR|CAMPUS|FORUM)"
# Feature tokens (fino a 2 occorrenze): 00s/OG/II/2/ADV/BOLD/INDOOR/MID/LOW/HI/CL
_FEATURE_TOK = r"(?:00S|00s|OG|II|2|ADV|BOLD|INDOOR|MID|LOW|HI|CL)"
# Target tokens (al massimo 1): J/K/C/W/M/EL/CF
_TARGET_TOK  = r"(?:J|K|C|W|M|EL|CF)"

RE_MODEL = re.compile(
    rf"\b({_BASE_MODELS}"
    rf"(?:\s+{_FEATURE_TOK}){{0,2}}"
    rf"(?:\s+{_TARGET_TOK})?"
    rf")\b",
    re.IGNORECASE,
)

def _normalize_model(raw: str) -> str:
    """Normalizza: spazio singolo, CAMPUS 00s, II vs 2, ordine 'base + feature + target'."""
    if not raw:
        return ""
    t = re.sub(r"\s+", " ", raw.upper()).strip()

    # Separa token
    parts = t.split(" ")
    base = []
    features = []
    target = []

    # ricostruisci base (può essere 'GAZELLE INDOOR' come feature? gestiamo sotto)
    i = 0
    if i < len(parts) and parts[i] in {"STAN", "SAMBA", "GAZELLE", "SUPERSTAR", "CAMPUS", "FORUM"}:
        if parts[i] == "STAN" and i + 1 < len(parts) and parts[i+1] == "SMITH":
            base = ["STAN", "SMITH"]; i += 2
        else:
            base = [parts[i]]; i += 1
    # trattiamo 'INDOOR' come feature per GAZELLE
    while i < len(parts):
        p = parts[i]
        if p in {"J","K","C","W","M","EL","CF"}:
            target = [p]; i += 1
        elif p in {"00S","00s","OG","II","2","ADV","BOLD","INDOOR","MID","LOW","HI","CL"}:
            features.append(p); i += 1
        else:
            # ignora token estranei
            i += 1

    # Normalizzazioni
    # 00S -> 00s (stilistica adidas)
    features = ["00s" if f in {"00S","00s"} else f for f in features]
    # 2 -> II (alcune etichette usano '2')
    features = ["II" if f == "2" else f for f in features]

    # Se base è GAZELLE e ha 'INDOOR' nei features, va bene come feature (uscita: "GAZELLE INDOOR ...")
    # Ordine: base + features (max 2) + target (max 1)
    out = " ".join(base + features + target).strip()

    # Aggiusta casi tipici
    # CAMPUS 00s: assicura minuscola 's'
    out = re.sub(r"\bCAMPUS 00S\b", "CAMPUS 00s", out)
    # Elimina duplicati consecutivi
    out = re.sub(r"( \b\w+\b)( \1\b)+", r"\1", out)

    return out
