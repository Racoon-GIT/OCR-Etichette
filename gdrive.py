import io, os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/cloud-platform"
]

def _creds():
    import json
    data = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    return service_account.Credentials.from_service_account_info(data, scopes=SCOPES)

def drive_svc():
    return build("drive", "v3", credentials=_creds(), cache_discovery=False)

def list_images(folder_id, page_size=50):
    svc = drive_svc()
    q = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed=false"
    res = svc.files().list(q=q, pageSize=page_size, fields="files(id, name, mimeType)").execute()
    return res.get("files", [])

def download_file(file_id, out_path):
    svc = drive_svc()
    req = svc.files().get_media(fileId=file_id)
    fh = io.FileIO(out_path, 'wb')
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return out_path

def move_file(file_id, to_folder_id):
    svc = drive_svc()
    file = svc.files().get(fileId=file_id, fields="parents").execute()
    prev_parents = ",".join(file.get("parents", []))
    svc.files().update(fileId=file_id, addParents=to_folder_id, removeParents=prev_parents, fields="id, parents").execute()
