from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# ---------- Utils ----------
def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default

def _lazy_worker():
    # Importi pesanti solo quando servono
    import worker
    return worker

def _lazy_drive():
    from gdrive import list_images
    return list_images

# ---------- Routes ----------
@app.get("/healthz")
def healthz():
    # Niente import pesanti qui: deve SEMPRE rispondere
    return "ok", 200

@app.route("/process", methods=["GET", "POST"])
def process():
    """
    Esegue un batch di elaborazione:
    - legge immagini dalla INBOX
    - OCR ibrido
    - scrive su Google Sheets
    - sposta file in PROCESSED/REVIEW
    Query param: ?limit=20 (opzionale)
    """
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
        # Log essenziale in risposta (per debug veloce)
        return jsonify({"error": "PROCESS_FAILED", "detail": str(e)}), 500

@app.get("/debug/drive-inbox")
def debug_drive_inbox():
    """
    Ritorna cosa vede la Drive API nella cartella INBOX.
    Utile se /process restituisce processed: 0.
    """
    try:
        inbox_id = os.environ.get("DRIVE_INBOX_FOLDER_ID", "")
        if not inbox_id:
            return jsonify({"error": "MISSING_ENV", "detail": "DRIVE_INBOX_FOLDER_ID non impostata"}), 400

        list_images = _lazy_drive()
        files = list_images(inbox_id, page_size=50)
        # Risposta compatta
        return jsonify({
            "folder": inbox_id,
            "count": len(files),
            "files": [{"id": f.get("id"), "name": f.get("name")} for f in files]
        }), 200
    except Exception as e:
        return jsonify({"error": "DRIVE_DEBUG_FAILED", "detail": str(e)}), 500

# ---------- Main (solo per run locale) ----------
if __name__ == "__main__":
    # In locale puoi usare una PORT fissa; su Render usiamo $PORT
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
