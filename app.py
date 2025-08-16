from flask import Flask, request, jsonify
import os
from worker import process_batch

app = Flask(__name__)

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.post("/process")
def process():
    try:
        limit = int(request.args.get("limit", os.environ.get("BATCH_LIMIT", "20")))
    except ValueError:
        limit = 20
    results = process_batch(limit=limit)
    return jsonify({"processed": len(results), "results": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), debug=False)
