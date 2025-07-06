import logging
import os
import threading
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from service_account import (
    append_bot_lead, get_watch_database,
    get_marques_by_sexe, get_modeles_by_sexe_marque,
    get_finitions, get_prix_achat
)

# === Logger ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# === Environ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8443))

# === States ===
(
    NOM, TEL, VILLE, ADRESSE, SEXE,
    MARQUE, MODELE, FINITION, BOITE, PRIX_VENTE, COMMENTAIRE
) = range(11)

# Charger la base montres
watch_db = get_watch_database()
AUTHORIZED_USERS = [5427202496, 1580306191]

# === Étapes du bot Telegram ===
async def start_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in AUTHORIZED_USERS:
        return
    await update.message.reply_text("📋 Nom du client ?")
    return NOM

async def get_nom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['nom'] = update.message.text
    await update.message.reply_text("📞 Numéro de téléphone ?")
    return TEL

async def get_tel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tel'] = update.message.text
    await update.message.reply_text("🏙️ Ville ?")
    return VILLE

async def get_ville(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ville'] = update.message.text
    await update.message.reply_text("📍 Adresse ?")
    return ADRESSE

async def get_adresse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['adresse'] = update.message.text
    await update.message.reply_text("👤 Sexe ?", reply_markup=ReplyKeyboardMarkup([["Homme", "Femme"]], one_time_keyboard=True))
    return SEXE

async def get_sexe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sexe = update.message.text.strip().capitalize()
    if sexe not in ["Homme", "Femme"]:
        await update.message.reply_text("❗ Choix invalide. Merci de choisir Homme ou Femme.")
        return SEXE
    context.user_data['sexe'] = sexe
    marques = get_marques_by_sexe(watch_db, sexe)
    keyboard = [marques[i:i+2] for i in range(0, len(marques), 2)]
    await update.message.reply_text("⌚ Marque ?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return MARQUE

async def get_marque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    marque = update.message.text
    context.user_data['marque'] = marque
    modele_list = get_modeles_by_sexe_marque(watch_db, context.user_data['sexe'], marque)
    keyboard = [modele_list[i:i+2] for i in range(0, len(modele_list), 2)]
    await update.message.reply_text("📎 Modèle ?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return MODELE

async def get_modele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modele = update.message.text
    context.user_data['modele'] = modele
    finition_list = get_finitions(watch_db, context.user_data['sexe'], context.user_data['marque'], modele)
    keyboard = [finition_list[i:i+2] for i in range(0, len(finition_list), 2)]
    await update.message.reply_text("🎨 Finition ?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return FINITION

async def get_finition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['finition'] = update.message.text
    await update.message.reply_text("🎁 Type de boîte ?", reply_markup=ReplyKeyboardMarkup([["Simple", "Originale"]], one_time_keyboard=True))
    return BOITE

async def get_boite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['boite'] = update.message.text
    await update.message.reply_text("💰 Prix de vente au client ?")
    return PRIX_VENTE

async def get_prix_vente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prix_vente'] = update.message.text
    data = context.user_data
    prix_achat = get_prix_achat(
        watch_db,
        data['sexe'],
        data['marque'],
        data['modele'],
        data['finition'],
        data['boite']
    )
    context.user_data['prix_achat'] = prix_achat
    await update.message.reply_text("📝 Un commentaire (facultatif) ? (ex: livraison le vendredi 05/07)")
    return COMMENTAIRE

async def get_commentaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['commentaire'] = update.message.text
    data = context.user_data
    resume = (
        f"✅ Résumé de la commande :\n"
        f"👤 Nom : {data['nom']}\n"
        f"📞 Téléphone : {data['tel']}\n"
        f"🏙️ Ville : {data['ville']}\n"
        f"📍 Adresse : {data['adresse']}\n"
        f"👥 Sexe : {data['sexe']}\n"
        f"⌚ Marque : {data['marque']}\n"
        f"📎 Modèle : {data['modele']}\n"
        f"🎨 Finition : {data['finition']}\n"
        f"🎁 Boîte : {data['boite']}\n"
        f"💰 Vente : {data['prix_vente']} | Achat : {data['prix_achat']}"
    )
    if data.get("commentaire"):
        resume += f"\n📝 Commentaire : {data['commentaire']}"

    await update.message.reply_text(resume + "\n\n✅ Merci, la commande est enregistrée.")
    append_bot_lead(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Commande annulée.")
    return ConversationHandler.END

# === Serveur Flask pour Webhook Woo ===
from flask import Flask, request
from woocommerce_orders import handle_woocommerce_webhook

flask_app = Flask(__name__)

@flask_app.route('/woocommerce/webhook', methods=['GET', 'POST'])
def woocommerce_webhook():
    if request.method == 'GET':
        return "✅ Webhook actif (GET reçu)", 200
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        print("📦 Webhook reçu :", data)
    except Exception as e:
        return f"❌ Erreur lecture corps : {e}", 400

    handle_woocommerce_webhook(data)
    return "✅ Webhook reçu (POST)", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

# === Main ===
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.ChatType.GROUPS, start_conv)],
        states={
            NOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nom)],
            TEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tel)],
            VILLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ville)],
            ADRESSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_adresse)],
            SEXE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sexe)],
            MARQUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_marque)],
            MODELE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_modele)],
            FINITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_finition)],
            BOITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_boite)],
            PRIX_VENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prix_vente)],
            COMMENTAIRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_commentaire)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )
