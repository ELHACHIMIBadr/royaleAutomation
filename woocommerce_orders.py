import os
import requests
from datetime import date
from dateutil import parser
from service_account import (
    get_leads_data, append_woocommerce_lead,
    get_watch_database, get_prix_achat,
    get_last_client_number, get_sheet
)

# === Chargement base produit
watch_db = get_watch_database()

# === Accès API WooCommerce
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

    try:
        response = requests.get(url, auth=auth, params=params)
        response.raise_for_status()
        orders = response.json()
    except Exception as e:
        print(f"[WooCommerce Worker] ❌ Erreur de récupération des commandes : {e}")
        return

    # Récupération leads existants
    existing_leads = get_leads_data()
    existing_phones = {lead.get("Numéro") for lead in existing_leads}
    sheet = get_sheet()
    last_client_number = get_last_client_number(sheet)

    today = date.today()

    for order in orders:
        try:
            order_date = parser.parse(order.get('date_created')).date()
            if order_date != today:
                continue

            billing = order.get("billing", {})
            nom = f"{billing.get('first_name', '').strip()} {billing.get('last_name', '').strip()}".strip()
            tel = billing.get("phone", "").strip()
            ville = billing.get("city", "")
            adresse = billing.get("address_1", "")

            if not tel or not nom:
                continue

            # Détection doublon stricte sur ligne précédente uniquement
            if existing_leads:
                last_lead = existing_leads[-1]
                if last_lead.get("Numéro") == tel and last_lead.get("Nom") == nom:
                    continue

            items = order.get("line_items", [])
            if not items:
                continue

            produit = items[0]
            produit_name = produit.get("name", "")

            # Matching basé sur "modèle"
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

            # Insertion
            ligne = {
                "Date": parser.parse(order.get("date_created")).strftime("%d/%m/%Y"),
                "n client": last_client_number + 1,
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

            append_woocommerce_lead(ligne)
            last_client_number += 1

        except Exception as e:
            print(f"[WooCommerce Worker] ❌ Erreur lors du traitement d'une commande : {e}")
