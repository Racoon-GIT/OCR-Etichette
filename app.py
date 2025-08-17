# app.py
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default

def _lazy_worker():
    import worker  # import ritardato per evitare crash all’avvio
    return worker

def _lazy_drive():
    from gdrive import list_images
    return list_images

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

@app.get("/debug/drive-inbox")
def debug_drive_inbox():
    try:
        inbox_id = os.environ.get("DRIVE_INBOX_FOLDER_ID", "")
        if not inbox_id:
            return jsonify({"error": "MISSING_ENV", "detail": "DRIVE_INBOX_FOLDER_ID non impostata"}), 400
        list_images = _lazy_drive()
        files = list_images(inbox_id, page_size=50)
        return jsonify({
            "folder": inbox_id,
            "count": len(files),
            "files": [{"id": f.get("id"), "name": f.get("name")} for f in files]
        }), 200
    except Exception as e:
        return jsonify({"error": "DRIVE_DEBUG_FAILED", "detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), debug=False)
