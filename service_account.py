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

# === Ajouter une ligne dans Leads avec incrémentation automatique
def append_to_leads(data: dict):
    today = datetime.now().strftime('%d/%m/%Y')

    # Incrémentation automatique du n° client
    existing_rows = leads_sheet.get_all_values()
    next_id = len(existing_rows)  # en comptant l'en-tête

    ligne = [
        today,                          # ✅ Date en 1er
        next_id,                        # ✅ n° client en 2e
        data.get("nom", ""),            # Nom
        data.get("tel", ""),            # Numéro
        data.get("ville", ""),          # Ville
        data.get("adresse", ""),        # Adresse
        0,                              # Coût de livraison
        data.get("marque", ""),         # Montre
        data.get("modele", ""),         # Gamme (Modèle)
        data.get("finition", ""),       # Finition
        data.get("prix_achat", ""),     # Prix d'achat
        data.get("prix_vente", ""),     # Prix de vente
        "Confirmé",                     # Statut
        data.get("commentaire", "")     # ✅ Commentaire aligné
    ]

    leads_sheet.append_row(ligne)

# === Récupérer la base montres (normalisée)
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

# === Funnel dynamique ===

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
                return base  # fallback en cas d'erreur

    return ''
