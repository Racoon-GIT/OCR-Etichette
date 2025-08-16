import os, time, tempfile
from gdrive import list_images, download_file, move_file
from sheets import append_rows
from ocr import extract_fields

INBOX  = os.environ.get("DRIVE_INBOX_FOLDER_ID")
PROC   = os.environ.get("DRIVE_PROCESSED_FOLDER_ID")
REVIEW = os.environ.get("DRIVE_REVIEW_FOLDER_ID")

def process_batch(limit=20):
    files = list_images(INBOX, page_size=limit)
    results = []
    rows = []
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    for f in files:
        fid, name = f["id"], f["name"]
        with tempfile.TemporaryDirectory() as td:
            local = os.path.join(td, name)
            download_file(fid, local)

            model, articolo, colore, size, barcode, score, stato = extract_fields(local)

            rows.append([ts, name, model, articolo, colore, size, barcode, score, stato])

            # move file
            dest = PROC if stato == "OK" else REVIEW
            try:
                move_file(fid, dest)
            except Exception as e:
                results.append({"file": name, "error": str(e)})
                continue

            results.append({"file": name, "stato": stato, "score": score})
    if rows:
        append_rows(rows)
    return results

if __name__ == "__main__":
    out = process_batch(limit=int(os.environ.get("BATCH_LIMIT", "20")))
    print({"processed": len(out)})
