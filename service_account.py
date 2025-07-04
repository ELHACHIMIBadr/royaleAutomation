import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

# === Constantes ===
SPREADSHEET_NAME = 'Commande Royale Heure'
LEADS_SHEET_NAME = 'Leads'
WATCH_DB_SHEET_NAME = 'Base de données montres RH'

# === Lecture du fichier JSON depuis Render Secret Mount
with open('/etc/secrets/royaleheurebot-cd5722cbdc55.json', 'r') as f:
    creds_dict = json.load(f)

# === Scopes requis (Sheets + Drive pour open() par nom)
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

# === Création des credentials et autorisation
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
sh = gc.open(SPREADSHEET_NAME)

# === Accès aux feuilles
leads_sheet = sh.worksheet(LEADS_SHEET_NAME)
watch_db_sheet = sh.worksheet(WATCH_DB_SHEET_NAME)

# === Ajouter ligne dans Leads
def append_to_leads(data: list):
    today = datetime.now().strftime('%d/%m/%Y')
    leads_sheet.append_row([today] + data)

# === Récupérer base montres
def get_watch_database():
    records = watch_db_sheet.get_all_records()
    normalized_records = []

    for row in records:
        normalized_row = {
            key.strip().lower().replace(" ", "_"): value
            for key, value in row.items()
        }
        normalized_records.append(normalized_row)

    return normalized_records

