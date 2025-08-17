# app.py
from flask import Flask, request, jsonify
import os, json

app = Flask(__name__)

# -------- lazy loaders --------
def _lazy_worker():
    import worker
    return worker

def _lazy_drive():
    from gdrive import list_images, download_file
    return list_images, download_file

def _lazy_ocr():
    from ocr import load_image, tesseract_texts, vision_ocr, extract_fields
    return load_image, tesseract_texts, vision_ocr, extract_fields

def _env_int(name: str, default: int) -> int:
    try: return int(os.environ.get(name, str(default)))
    except: return default

# -------- routes --------
@app.get("/healthz")
def healthz():
    return "ok", 200

@app.route("/process", methods=["GET", "POST"])
def process():
    try:
        limit_qs = request.args.get("limit")
        limit = int(limit_qs) if limit_qs is not None else _env_int("BATCH_LIMIT", 20)
    except ValueError:
        limit = 20
    worker = _lazy_worker()
    results = worker.process_batch(limit=limit)
    return jsonify({"processed": len(results), "results": results}), 200

@app.get("/debug/env")
def debug_env():
    present = {k: (k in os.environ) for k in [
        "GOOGLE_CREDENTIALS_JSON","DRIVE_INBOX_FOLDER_ID",
        "DRIVE_PROCESSED_FOLDER_ID","DRIVE_REVIEW_FOLDER_ID","SHEET_ID"
    ]}
    sa_email = ""
    try:
        info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
        sa_email = info.get("client_email","")
    except Exception:
        pass
    return {"env_present": present, "service_account_email": sa_email}, 200

@app.get("/debug/drive-inbox")
def debug_drive_inbox():
    list_images, _ = _lazy_drive()
    inbox_id = os.environ.get("DRIVE_INBOX_FOLDER_ID","")
    if not inbox_id:
        return {"error":"MISSING_ENV","detail":"DRIVE_INBOX_FOLDER_ID non impostata"}, 400
    files = list_images(inbox_id, page_size=100)
    return {"folder": inbox_id, "count": len(files),
            "files": [{"id": f.get("id"), "name": f.get("name")} for f in files]}, 200

@app.get("/debug/drive-search")
def debug_drive_search():
    from gdrive import search_any
    name = request.args.get("name","")
    if not name:
        return {"error":"MISSING_PARAM","detail":"use ?name=..."}, 400
    hits = search_any(name, page_size=50)
    return {"query": name, "count": len(hits),
            "files":[{"id":x.get("id"),"name":x.get("name"),"mimeType":x.get("mimeType")} for x in hits]}, 200

@app.get("/debug/ocr")
def debug_ocr():
    """
    Esegue OCR grezzo su un file di Drive e/o ritorna un campo specifico.
    Query:
      - id (obbl.): fileId di Drive
      - field (opz.): modello|articolo|colore|taglia_fr|barcode|confidenza|stato
    """
    file_id = request.args.get("id")
    if not file_id:
        return {"error":"MISSING_PARAM","detail":"use ?id=<fileId>&field=..."}, 400

    list_images, download_file = _lazy_drive()
    load_image, tesseract_texts, vision_ocr, extract_fields = _lazy_ocr()

    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        local = os.path.join(td, "img")
        download_file(file_id, local)

        # OCR
        pil = load_image(local)
        t_gen, t_dig = tesseract_texts(pil)
        v_gen, v_dig = vision_ocr(local)
        model, articolo, colore, size, barcode, score, stato = extract_fields(local)

    field = (request.args.get("field") or "").lower().strip()
    if field:
        mapping = {
            "modello": model, "articolo": articolo, "colore": colore,
            "taglia_fr": size, "barcode": barcode,
            "confidenza": score, "stato": stato
        }
        if field in mapping:
            return {"id": file_id, "field": field, "value": mapping[field]}, 200
        else:
            return {"error":"BAD_FIELD","detail":"use modello|articolo|colore|taglia_fr|barcode|confidenza|stato"}, 400

    return {
        "id": file_id,
        "tesseract": {"general": t_gen, "digits": t_dig},
        "vision": {"general": v_gen, "digits": v_dig},
        "parsed": {
            "modello": model, "articolo": articolo, "colore": colore,
            "taglia_fr": size, "barcode": barcode,
            "confidenza": score, "stato": stato
        }
    }, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","10000")), debug=False)
