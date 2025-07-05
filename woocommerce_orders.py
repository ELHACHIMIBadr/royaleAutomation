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

# === Construit une requête vers WooCommerce (commandes)
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
        # Informations client
        billing = order.get("billing", {})
        nom = billing.get("first_name", "") + " " + billing.get("last_name", "")
        tel = billing.get("phone", "").strip()
        ville = billing.get("city", "")
        adresse = billing.get("address_1", "")

        if tel in existing_phones:
            continue  # déjà traité

        # Récupération des données produit
        items = order.get("line_items", [])
        if not items:
            continue

        produit = items[0]
        produit_name = produit.get("name", "")

        # Déduction des champs depuis le nom du produit
        marque = ""
        modele = ""
        finition = ""
        for row in watch_db:
            if row['produit'].lower() in produit_name.lower():
                marque = row['marque']
                modele = row['modèle']  # ✅ Correction : on mappe "modèle" pas "gamme"
                finition = row['finition']
                break

        if not all([marque, modele, finition]):
            continue  # Si on ne peut pas mapper correctement, on ignore

        # Calcul du prix d’achat avec "Simple" par défaut
        prix_achat = get_prix_achat(
            watch_db,
            row.get('sexe', 'Homme'),  # fallback
            marque,
            modele,
            finition,
            "Simple"
        )

        # Insertion dans Google Sheets
        ligne = {
            "Date": datetime.now().strftime('%d/%m/%Y'),
            "Nom": nom,
            "Numéro": tel,
            "Ville": ville,
            "Adresse": adresse,
            "Marque": marque,
            "Gamme": modele,           # ✅ correspond à la colonne Modèle dans la base
            "Finition": finition,
            "Prix achat": prix_achat,
            "Prix vente": order.get("total", ""),
            "Statut": "À confirmer",
            "Commentaire": f"Commande WooCommerce #{order.get('id')}"
        }

        append_woocommerce_lead(ligne)
