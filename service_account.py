import gspread
from datetime import datetime

# Nom exact du fichier JSON (il doit être à la racine du projet)
SERVICE_ACCOUNT_FILE = 'royaleheurebot-43c46ef6f78f.json'

# Nom exact du Google Sheet
SPREADSHEET_NAME = 'Commande Royale Heure'

# Noms des onglets
LEADS_SHEET_NAME = 'Leads'
WATCH_DB_SHEET_NAME = 'Base de données montres RH'

# Connexion à Google Sheets
gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
sh = gc.open(SPREADSHEET_NAME)

# Accès aux feuilles
leads_sheet = sh.worksheet(LEADS_SHEET_NAME)
watch_db_sheet = sh.worksheet(WATCH_DB_SHEET_NAME)

# Fonction utilitaire pour ajouter une ligne dans Leads
def append_to_leads(data: list):
    today = datetime.now().strftime('%d/%m/%Y')
    leads_sheet.append_row([today] + data)

# Fonction utilitaire pour récupérer la base des montres (liste de dicts)
def get_watch_database():
    records = watch_db_sheet.get_all_records()
    return records  # Liste de dictionnaires
