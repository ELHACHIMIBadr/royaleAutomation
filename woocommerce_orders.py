from dateutil import parser

# === Gère l'incrémentation du champ "n client"
def get_next_client_number(leads):
    if not leads:
        return 1
    try:
        last = leads[-1]
        return int(last.get("n client", "0")) + 1
    except:
        return 1



import os
import requests
from datetime import datetime, date
from service_account import (
    get_leads_data, append_woocommerce_lead,
    get_watch_database, get_prix_achat
)

# === Chargement de la base produit
watch_db = get_watch_database()

# === API WooCommerce
WC_BASE_URL = os.environ.get("WC_BASE_URL")
WC_KEY = os.environ.get("WC_KEY")
WC_SECRET = os.environ.get("WC_SECRET")

def fetch_woocommerce_orders():
    url = f"{WC_BASE_URL}/wp-json/wc/v3/orders"
    auth = (WC_KEY, WC_SECRET)
    params = {
        "per_page": 20,
        "orderby": "date",
        "order": "desc"
    }

    response = requests.get(url, auth=auth, params=params)
    orders = response.json()

    existing_leads = get_leads_data()
    existing_phones = {lead.get("Numéro") for lead in existing_leads}

    today = date.today()
    for order in orders:
        order_date = parser.parse(order.get('date_created')).date()
        if order_date != today:
            continue
        billing = order.get("billing", {})
        nom = billing.get("first_name", "") + " " + billing.get("last_name", "")
        tel = billing.get("phone", "").strip()
        ville = billing.get("city", "")
        adresse = billing.get("address_1", "")

        if tel in existing_phones:
            continue

        items = order.get("line_items", [])
        if not items:
            continue

        produit = items[0]
        produit_name = produit.get("name", "")

        # Tentative de mappage automatique
        matched_row = next((
            row for row in watch_db
            if row.get("modèle", "").lower() in produit_name.lower()
        ), None)

        if not matched_row:
            continue

        marque = matched_row.get("marque", "")
        modele = matched_row.get("modèle", "")
        finition = matched_row.get("finition", "")
        sexe = matched_row.get("sexe", "Homme")

        if not all([marque, modele, finition]):
            continue

        prix_achat = get_prix_achat(
            watch_db, sexe, marque, modele, finition, "Simple"
        )

        ligne = {
            "Date": parser.parse(order.get("date_created")).strftime("%d/%m/%Y"),
            "n client": get_next_client_number(existing_leads),
            "Nom": nom,
            "Numéro": tel,
            "Ville": ville,
            "Adresse": adresse,
            "Marque": marque,
            "Modèle": modele,
            "Finition": finition,
            "Prix achat": prix_achat,
            "Prix vente": order.get("total", ""),
            "Statut": "À confirmer",
            "Commentaire": f"Commande WooCommerce #{order.get('id')}"
        }

        from service_account import get_last_client_number
        sheet = get_sheet()
        last_number = get_last_client_number(sheet)
        ligne["n client"] = last_number + 1
        append_woocommerce_lead(ligne)
