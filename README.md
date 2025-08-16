# Render OCR Labels – Drive → Tesseract/Vision → Google Sheets

Backend Python pronto per **Render.com** con OCR ibrido:
- **Tesseract** (gratis) + **pyzbar** (barcode)
- **Google Vision API** (fallback a consumo)
- Input da **Google Drive** (cartella INBOX)
- Output su **Google Sheets**
- Smistamento file in **PROCESSED** / **REVIEW**

## 1) Variabili d'ambiente (Render → Settings → Environment)
- `GOOGLE_CREDENTIALS_JSON`  → incolla il contenuto JSON della chiave del Service Account
- `DRIVE_INBOX_FOLDER_ID`    → ID cartella INBOX su Drive
- `DRIVE_PROCESSED_FOLDER_ID`→ ID cartella PROCESSED
- `DRIVE_REVIEW_FOLDER_ID`   → ID cartella REVIEW
- `SHEET_ID`                 → ID del Google Sheet di output
- (opz) `BATCH_LIMIT`        → default 20
- (opz) `SCORE_OK_THRESHOLD` → default 75
- (opz) `REQUIRE_BARCODE`    → "1" per richiedere barcode per OK

> Condividi le 3 cartelle e lo Sheet con l'**email del Service Account** (permesso **Editor**).

## 2) Deploy su Render
1. **New +** → **Web Service** → collega il repo
2. Runtime: **Docker** (usa il Dockerfile incluso)
3. Porta: usa la `PORT` impostata (10000)
4. Deploy

### Endpoint disponibili
- `GET /healthz`    → check salute
- `POST /process?limit=20` → trigger manuale batch

## 3) Cron Job su Render
- **New +** → **Cron Job**
- Command: `python worker.py`
- Schedule: ogni 5 minuti (o come preferisci)
- Imposta **stesse variabili d'ambiente** del Web Service

## 4) Colonne sullo Sheet
`Timestamp | Image_File | Modello | Articolo | Colore | Taglia_FR | Barcode | Confidenza | Stato`

## 5) Suggerimenti qualità
- Carica **solo l'etichetta** (dritta, a fuoco, luce uniforme)
- Formati **JPG/PNG/HEIC** (HEIC supportato via pillow-heif)
- Se vedi molte righe in REVIEW, alza la qualità delle foto o abilita Vision fallback

## 6) Sicurezza
- Non committare credenziali: usa solo `GOOGLE_CREDENTIALS_JSON` come **env var**.
- Limita i permessi del Service Account a Drive/Sheets/Vision.
