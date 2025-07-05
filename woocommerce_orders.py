
import logging
from service_account import (
    get_watch_database,
    get_leads_data,
    append_woocommerce_order_to_leads
)

logger = logging.getLogger(__name__)

def process_woocommerce_orders():
    try:
        logger.info("[WooCommerce Worker] 🚀 Démarrage du traitement des commandes WooCommerce")

        # Base de données montres RH
        watch_db = get_watch_database()
        leads_data = get_leads_data()
        last_client_number = 0

        if leads_data:
            try:
                last_client_number = int(leads_data[-1].get("n client", 0))
            except Exception:
                last_client_number = 0

        # Simule les commandes WooCommerce ici
        commandes = [
            {
                "nom": "Charame Abdelmejid",
                "numero": "0661624792",
                "ville": "cityTestMock",
                "adresse": "Kenitra",
                "commentaire": "Commande WooCommerce",
                "prix_vente": 450,
                "statut": "À confirmer",
                "boite": "Simple",
                "nom_woocommerce": "Cartier Ballon Bleu 33mm - Rose"
            },
            {
                "nom": "Hamza",
                "numero": "0633823315",
                "ville": "cityTestMock",
                "adresse": "Bd ahmed mekouar res ritaje ain sebaa casablanca",
                "commentaire": "Commande WooCommerce",
                "prix_vente": 550,
                "statut": "À confirmer",
                "boite": "Originale",
                "nom_woocommerce": "Cartier Ballon Bleu 33mm - Argent"
            }
        ]

        for i, ligne in enumerate(commandes):
            nom_woo = str(ligne.get("nom_woocommerce", "")).strip()
            boite_type = str(ligne.get("boite", "Simple")).strip().capitalize()

            # Rechercher la montre correspondante
            match = next(
                (w for w in watch_db if str(w.get("nom sur woocommerce", "")).strip().lower() == nom_woo.lower()),
                None
            )

            if not match:
                logger.warning(f"🔍 Aucun match trouvé pour '{nom_woo}'")
                continue

            # Extraire infos depuis base montres RH
            marque = match.get("marque", "")
            modele = match.get("modèle", "")  # ✅ Correction ici
            finition = match.get("finition", "")
            prix_achat_base = float(match.get("prix achat montre", 0))
            prix_boite = float(match.get("prix boite simple", 0)) if boite_type == "Simple" else float(match.get("prix boite original", 0))
            prix_achat = prix_achat_base + prix_boite

            # Construction de la ligne à insérer
            ligne_sheet = {
                "date": None,  # sera ajouté dans append
                "n client": last_client_number + i + 1,
                "nom": ligne.get("nom", ""),
                "numéro": str(ligne.get("numero", "")),
                "ville": ligne.get("ville", ""),
                "adresse": ligne.get("adresse", ""),
                "cout de livraison": 0,
                "montre": marque,
                "gamme": modele,
                "finition": finition,
                "prix d'achat": prix_achat,
                "prix de vente": ligne.get("prix_vente", 0),
                "statut": ligne.get("statut", "À confirmer"),
                "commentaire": ligne.get("commentaire", ""),
            }

            append_woocommerce_order_to_leads(ligne_sheet)

        logger.info("[WooCommerce Worker] ✅ Commandes WooCommerce ajoutées avec succès")

    except Exception as e:
        logger.error(f"[WooCommerce Worker] ❌ Erreur : {e}")
