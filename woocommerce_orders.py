
import os
import requests
from datetime import datetime
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

    for order in orders:
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
            "Date": datetime.now().strftime('%d/%m/%Y'),
            "Nom": nom,
            "Numéro": tel,
            "Ville": ville,
            "Adresse": adresse,
            "Marque": marque,
            "Gamme": modele,
            "Finition": finition,
            "Prix achat": prix_achat,
            "Prix vente": order.get("total", ""),
            "Statut": "À confirmer",
            "Commentaire": f"Commande WooCommerce #{order.get('id')}"
        }

        append_woocommerce_lead(ligne)
