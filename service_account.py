import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

# === Constantes ===
SPREADSHEET_NAME = 'Commande Royale Heure'
LEADS_SHEET_NAME = 'Leads'
WATCH_DB_SHEET_NAME = 'Base de données montres RH'

# === Lecture depuis le fichier secret fourni par Render
with open('/etc/secrets/royaleheurebot-6215c544a8d4', 'r') as f:
    creds_dict = json.load(f)

# === Création des credentials
scopes = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)

# === Connexion à Google Sheets
gc = gspread.authorize(credentials)
sh = gc.open(SPREADSHEET_NAME)

leads_sheet = sh.worksheet(LEADS_SHEET_NAME)
watch_db_sheet = sh.worksheet(WATCH_DB_SHEET_NAME)

# === Ajouter ligne dans Leads
def append_to_leads(data: list):
    today = datetime.now().strftime('%d/%m/%Y')
    leads_sheet.append_row([today] + data)

# === Récupérer base montres
def get_watch_database():
    return watch_db_sheet.get_all_records()
