import os, json
import gspread
from google.oauth2.service_account import Credentials

def _client():
    data = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = Credentials.from_service_account_info(
        data,
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    return gspread.authorize(creds)

def append_rows(rows):
    # rows: list of lists
    gc = _client()
    sh = gc.open_by_key(os.environ["SHEET_ID"])
    ws = sh.sheet1
    ws.append_rows(rows, value_input_option="RAW")
