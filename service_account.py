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

# === Scopes requis
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

# === Autorisation
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)
sh = gc.open(SPREADSHEET_NAME)

# === Accès aux feuilles
leads_sheet = sh.worksheet(LEADS_SHEET_NAME)
watch_db_sheet = sh.worksheet(WATCH_DB_SHEET_NAME)

# === Ajout ligne dans Leads avec "n client"
def append_to_leads(data: dict):
    today = datetime.now().strftime('%d/%m/%Y')

    # Déterminer le prochain numéro de client
    all_values = leads_sheet.get_all_values()
    last_row = all_values[-1] if len(all_values) > 1 else []
    last_client_number = 0

    try:
        if last_row and last_row[1].strip():
            last_client_number = int(last_row[1])
    except ValueError:
        last_client_number = 0

    new_client_number = last_client_number + 1

    ligne = [
        today,                              # Date
        new_client_number,                  # n client (auto)
        data.get("nom", ""),                # Nom
        data.get("tel", ""),                # Numéro
        data.get("ville", ""),              # Ville
        data.get("adresse", ""),            # Adresse
        0,                                  # Coût de livraison (fixe 0)
        data.get("marque", ""),             # Marque
        data.get("modele", ""),             # Modèle (anciennement gamme)
        data.get("finition", ""),           # Finition
        data.get("prix_achat", ""),         # Prix d’achat
        data.get("prix_vente", ""),         # Prix de vente
        "Confirmé",                         # Statut
        "",                                 # Adresse complète (optionnel)
        data.get("commentaire", ""),        # Commentaire (nouveau)
    ]

    leads_sheet.append_row(ligne)

# === Base de données des montres normalisée
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

# === Funnel dynamique
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

def get_prix_achat(watch_db, sexe, marque, modele, finition):
    for row in watch_db:
        if (
            row['sexe'].lower() == sexe.lower()
            and row['marque'].lower() == marque.lower()
            and row['modèle'].lower() == modele.lower()
            and row['finition'].lower() == finition.lower()
        ):
            return row.get('prix_achat_montre', '')
    return ''
