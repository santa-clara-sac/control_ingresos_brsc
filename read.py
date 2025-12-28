from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY = 'key_cromosoma.json'
SPREADSHEET_ID = '1SOVDMg8DcuM_dQmWaDWDfUXeUDx504zlGGw2gKeWit4'

# Autenticación
creds = service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Leer solo la tabla AUTOPARTES_DIAZ
result = sheet.values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='1!A:E'
).execute()

values = result.get('values', [])

df = pd.DataFrame(values)

print(df)
