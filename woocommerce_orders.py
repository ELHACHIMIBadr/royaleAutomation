import datetime
from service_account import (
    get_leads_data,
    append_woocommerce_lead,
    get_watch_database,
    get_prix_achat
)

# Charger la base de données produit dès le début
watch_db = get_watch_database()


def find_matching_product(product_name):
    """Essaie de trouver un produit correspondant dans la base de données."""
    product_name_lower = product_name.lower()

    for row in watch_db:
        modele = row.get("modèle", "").lower()
        if modele in product_name_lower:
            return row
    return None


def is_duplicate(leads, nom, numero):
    """Vérifie si la commande a déjà été insérée dans Google Sheets."""
    for lead in leads:
        if (
            lead.get("Nom", "").strip().lower() == nom.strip().lower()
            and lead.get("Numéro", "").strip() == numero.strip()
        ):
            return True
    return False


def get_next_client_number(leads):
    """Incrémente le numéro de client automatiquement."""
    if not leads:
        return 1
    try:
        last = leads[-1]
        return int(last.get("n client", "0")) + 1
    except:
        return 1


def handle_woocommerce_webhook(data):
    """Traite le webhook WooCommerce et insère une ligne dans Google Sheets."""

    # === 1. Extraction des données client ===
    billing = data.get("billing", {})
    nom = f"{billing.get('first_name', '').strip()} {billing.get('last_name', '').strip()}".strip()
    numero = billing.get("phone", "").strip()
    ville = billing.get("city", "").strip()
    adresse = billing.get("address_1", "").strip()
    date = datetime.datetime.now().strftime("%d/%m/%Y")

    # === 2. Vérifier les produits ===
    items = data.get("line_items", [])
    if not items:
        print("❌ Aucun produit dans la commande reçue.")
        return

    produit_name = items[0].get("name", "")
    matched_row = find_matching_product(produit_name)

    if not matched_row:
        print(f"❌ Produit non reconnu : {produit_name}")
        return

    marque = matched_row.get("marque", "")
    modele = matched_row.get("modèle", "")
    finition = matched_row.get("finition", "")
    sexe = matched_row.get("sexe", "Homme")

    # === 3. Vérification anti-doublon ===
    leads = get_leads_data()
    if is_duplicate(leads, nom, numero):
        print(f"⚠️ Commande déjà existante pour {nom} ({numero})")
        return

    # === 4. Générer prix d’achat ===
    prix_achat = get_prix_achat(modele, finition)

    # === 5. Générer n° client ===
    n_client = get_next_client_number(leads)

    # === 6. Insertion dans Google Sheets ===
    ligne = [
        date,
        n_client,
        nom,
        numero,
        ville,
        adresse,
        0,  # coût livraison
        marque,
        modele,
        finition,
        prix_achat,
        sexe,
        "Confirmé",  # statut par défaut
        "",  # commentaire
    ]

    append_woocommerce_lead(ligne)
    print(f"✅ Commande insérée : {nom} - {produit_name}")
