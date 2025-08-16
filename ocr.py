import os, json
import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageOps
import pillow_heif
from pyzbar.pyzbar import decode
from google.cloud import vision
from google.oauth2 import service_account
from parsing import parse_fields

def _vision_client():
    data = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = service_account.Credentials.from_service_account_info(data)
    return vision.ImageAnnotatorClient(credentials=creds)

def load_image(path):
    if path.lower().endswith((".heic",".heif")):
        heif = pillow_heif.read_heif(path)
        img = Image.frombytes(heif.mode, heif.size, heif.data, "raw")
        return img.convert("RGB")
    return Image.open(path).convert("RGB")

def tesseract_texts(pil):
    gray = ImageOps.autocontrast(pil.convert("L"))
    general = pytesseract.image_to_string(gray, config="--psm 6")
    digits  = pytesseract.image_to_string(gray, config="--psm 6 -c tessedit_char_whitelist=0123456789")
    return general, digits

def zbar_barcode(pil):
    cv = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    objs = decode(cv)
    for o in objs:
        try:
            s = o.data.decode("utf-8")
            if s.isdigit() and len(s) in (12,13):
                return s
        except Exception:
            pass
    return ""

def vision_ocr(path):
    cli = _vision_client()
    with open(path, "rb") as f:
        content = f.read()
    image = vision.Image(content=content)
    resp = cli.text_detection(image=image)
    text = resp.text_annotations[0].description if resp.text_annotations else ""
    digits = "".join(ch if ch.isdigit() else " " for ch in text)
    return text, digits

def extract_fields(path):
    pil = load_image(path)

    # 1) Tesseract (gratis)
    gen, dig = tesseract_texts(pil)
    model, articolo, colore, size, barcode, score, stato = parse_fields(gen, dig)

    # 2) ZBar barcode extra (gratis)
    if not barcode:
        try:
            b = zbar_barcode(pil)
            if b: barcode = b
        except Exception:
            pass

    # 3) Fallback Vision se mancano campi chiave
    if (score < int(os.environ.get("SCORE_OK_THRESHOLD", "75"))) or (not barcode and os.environ.get("REQUIRE_BARCODE","1")=="1"):
        v_gen, v_dig = vision_ocr(path)
        m2, a2, c2, s2, b2, sc2, st2 = parse_fields(v_gen, v_dig)
        model   = model or m2
        articolo= articolo or a2
        colore  = colore or c2
        size    = size or s2
        barcode = barcode or b2
        score   = max(score, sc2)
        stato   = "OK" if score >= int(os.environ.get("SCORE_OK_THRESHOLD", "75")) else "REVIEW"

    return model, articolo, colore, size, barcode, score, stato
