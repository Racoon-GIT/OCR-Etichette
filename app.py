from flask import Flask, request, jsonify
import os, json

app = Flask(__name__)

def _env_int(name: str, default: int) -> int:
    try: return int(os.environ.get(name, str(default)))
    except: return default

def _lazy_worker():
    import worker
    return worker

def _lazy_list_images():
    from gdrive import list_images, search_any
    return list_images, search_any

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
    try:
        worker = _lazy_worker()
        results = worker.process_batch(limit=limit)
        return jsonify({"processed": len(results), "results": results}), 200
    except Exception as e:
        return jsonify({"error": "PROCESS_FAILED", "detail": str(e)}), 500

@app.get("/debug/env")
def debug_env():
    present = {k: (k in os.environ) for k in [
        "GOOGLE_CREDENTIALS_JSON", "DRIVE_INBOX_FOLDER_ID",
        "DRIVE_PROCESSED_FOLDER_ID", "DRIVE_REVIEW_FOLDER_ID", "SHEET_ID"
    ]}
    # Tira fuori l'email del SA (se disponibile) senza mostrare tutta la chiave
    sa_email = ""
    try:
        info = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
        sa_email = info.get("client_email","")
    except Exception:
        pass
    return {"env_present": present, "service_account_email": sa_email}, 200

@app.get("/debug/drive-inbox")
def debug_drive_inbox():
    try:
        inbox_id = os.environ.get("DRIVE_INBOX_FOLDER_ID", "")
        if not inbox_id:
            return jsonify({"error": "MISSING_ENV", "detail": "DRIVE_INBOX_FOLDER_ID non impostata"}), 400
        list_images, _ = _lazy_list_images()
        files = list_images(inbox_id, page_size=100)
        return jsonify({
            "folder": inbox_id,
            "count": len(files),
            "files": [{"id": f.get("id"), "name": f.get("name")} for f in files]
        }), 200
    except Exception as e:
        return jsonify({"error": "DRIVE_DEBUG_FAILED", "detail": str(e)}), 500

@app.get("/debug/drive-search")
def debug_drive_search():
    # Cerca per nome in allDrives: utile per trovare ID cartelle/file
    qname = request.args.get("name","")
    if not qname:
        return {"error":"MISSING_PARAM","detail":"use ?name=qualcosa"}, 400
    try:
        _, search_any = _lazy_list_images()
        hits = search_any(qname, page_size=50)
        return {"query": qname, "count": len(hits),
                "files":[{"id":x.get("id"),"name":x.get("name"),"mimeType":x.get("mimeType")} for x in hits]}, 200
    except Exception as e:
        return {"error":"SEARCH_FAILED","detail":str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","10000")), debug=False)
