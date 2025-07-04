# woocommerce_orders.py

import requests
from datetime import datetime, timedelta
from service_account import get_watch_database, get_leads_data, append_to_leads

# === WooCommerce config ===
STORE_URL = "https://royaleheure.com"
CONSUMER_KEY = "ck_7bc8553017932c95d0b4cb04caba6998ebf61979"
CONSUMER_SECRET = "cs_c14cfac8daf38dcee3848290a1a79998d58943d1"
API_URL = f"{STORE_URL}/wp-json/wc/v3/orders"

def fetch_woocommerce_orders():
    print("📦 Récupération des commandes WooCommerce du jour...")

    # Récupérer les commandes passées aujourd’hui uniquement
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_iso = today.isoformat()

    response = requests.get(
        API_URL,
        auth=(CONSUMER_KEY, CONSUMER_SECRET),
        params={"per_page": 100, "orderby": "date", "order": "desc", "after": today_iso}
    )

    if response.status_code != 200:
        print("❌ Erreur API WooCommerce :", response.status_code, response.text)
        return

    orders = response.json()
    watch_db = get_watch_database()
    leads_data = get_leads_data()

    for order in orders:
        # Extraire infos client
        nom_client = f"{order['billing']['first_name']} {order['billing']['last_name']}".strip()
        numero = order['billing'].get('phone', '').strip()
        ville = order['billing'].get('city', '').strip()
        adresse = order['billing'].get('address_1', '').strip()
        prix_vente = float(order['total'])
        date_commande = datetime.strptime(order['date_created'][:10], "%Y-%m-%d").strftime("%d/%m/%Y")

        if not order['line_items']:
            print(f"⚠️ Commande sans produit : {order['id']}")
            continue

        produit_nom = order['line_items'][0]['name'].strip()

        # Matching produit dans la base RH
        matched_watch = next(
            (item for item in watch_db if item.get('nom sur woocommerce', '').strip() == produit_nom),
            None
        )

        if not matched_watch:
            print(f"⚠️ Produit non reconnu dans la base RH : {produit_nom}")
            continue

        # Vérification anti-doublon sur la même journée
        already_exists = any(
            row.get('Nom', '').strip() == nom_client and
            row.get('Numéro', '').strip() == numero and
            row.get('Gamme', '').strip() == matched_watch.get('modele', '').strip() and
            row.get('Finition', '').strip() == matched_watch.get('finition', '').strip() and
            row.get('Date', '').strip() == date_commande
            for row in leads_data
        )

        if already_exists:
            print(f"⛔ Doublon ignoré : {nom_client} | {produit_nom}")
            continue

        # Construction de la ligne à insérer
        row = {
            'Date': date_commande,
            'Nom': nom_client,
            'Numéro': numero,
            'Ville': ville,
            'Adresse': adresse,
            'Sexe': matched_watch.get('sexe', ''),
            'Marque': matched_watch.get('marque', ''),
            'Gamme': matched_watch.get('modele', ''),
            'Finition': matched_watch.get('finition', ''),
            'Prix achat': matched_watch.get('prix achat montre', ''),
            'Prix vente': prix_vente,
            'Statut': 'À confirmer',
            'Commentaire': 'Commande WooCommerce'
        }

        append_to_leads(row)
        print(f"✅ Commande insérée : {nom_client} | {produit_nom}")
