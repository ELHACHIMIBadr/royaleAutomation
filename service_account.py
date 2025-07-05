
def get_next_client_number(leads):
    if not leads:
        return 1
    try:
        last = leads[-1]
        return int(last.get("n client", "0")) + 1
    except:
        return 1

def is_duplicate(last_row, new_row):
    if not last_row:
        return False
    return (
        last_row.get("Nom", "").strip().lower() == new_row.get("Nom", "").strip().lower() and
        last_row.get("Numéro", "").strip() == new_row.get("Numéro", "").strip() and
        last_row.get("Modèle", "").strip().lower() == new_row.get("Modèle", "").strip().lower()
    )


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

# === BOT TELEGRAM : Ajouter une ligne dans Leads avec incrémentation automatique
def append_bot_lead(data: dict):
    today = datetime.now().strftime('%d/%m/%Y')
    existing_rows = leads_sheet.get_all_values()
    next_id = len(existing_rows)  # en comptant l'en-tête

    ligne = [
        today,                          # ✅ Date
        next_id,                        # ✅ n° client
        data.get("nom", ""),
        data.get("tel", ""),
        data.get("ville", ""),
        data.get("adresse", ""),
        0,
        data.get("marque", ""),
        data.get("modele", ""),         # Modèle
        data.get("finition", ""),
        data.get("prix_achat", ""),
        data.get("prix_vente", ""),
        "Confirmé",
        data.get("commentaire", "")
    ]

    leads_sheet.append_row(ligne)

# === WooCommerce : Ajouter une ligne dans Leads (sans numéro client)
def append_woocommerce_lead(row_data: dict):
    ligne = [
        row_data.get("Date", ""),
        "",  # n° client vide
        row_data.get("Nom", ""),
        row_data.get("Numéro", ""),
        row_data.get("Ville", ""),
        row_data.get("Adresse", ""),
        0,
        row_data.get("Marque", ""),
        row_data.get("Modèle", ""),  # ✅ Clé correcte ici
        row_data.get("Finition", ""),
        row_data.get("Prix achat", ""),
        row_data.get("Prix vente", ""),
        row_data.get("Statut", ""),
        row_data.get("Commentaire", "")
    ]

    leads_sheet.append_row(ligne)

# === WATCH RH : Récupérer la base montres
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

# === FUNNEL DYNAMIQUE
def get_marques_by_sexe(watch_db, sexe):
    return sorted(set(
        row['marque'] for row in watch_db
        if row['sexe'].lower() == sexe.lower()
    ))

def get_modeles_by_sexe_marque(watch_db, sexe, marque):
    return sorted(set(
        row['modèle'] for row in watch_db
        if row['sexe'].lower() == sexe.lower()
        and row['marque'].lower() == marque.lower()
    ))

def get_finitions(watch_db, sexe, marque, modele):
    return sorted(set(
        row['finition'] for row in watch_db
        if row['sexe'].lower() == sexe.lower()
        and row['marque'].lower() == marque.lower()
        and row['modèle'].lower() == modele.lower()
    ))

# === Calcul du prix d'achat total (montre + boîte)
def get_prix_achat(watch_db, sexe, marque, modele, finition, boite):
    for row in watch_db:
        if (
            row['sexe'].lower() == sexe.lower()
            and row['marque'].lower() == marque.lower()
            and row['modèle'].lower() == modele.lower()
            and row['finition'].lower() == finition.lower()
        ):
            base = row.get('prix_achat_montre', 0)
            if boite.lower() == "simple":
                supplement = row.get('prix_boite_simple', 0)
            elif boite.lower() == "originale":
                supplement = row.get('prix_boite_original', 0)
            else:
                supplement = 0

            try:
                return float(base) + float(supplement)
            except:
                return base

    return ''

# === Récupération des données actuelles pour vérification des doublons WooCommerce
def get_leads_data():
    records = leads_sheet.get_all_records()
    return records
