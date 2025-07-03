import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from service_account import append_to_leads, get_watch_database

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
    MARQUE, GAMME, FINITION, BOITE, PRIX_VENTE
) = range(10)

# Charger la base montres
watch_db = get_watch_database()

# IDs autorisés à déclencher le bot
AUTHORIZED_USERS = [5427202496, 1580306191]  # remplace-les par tes ID

# === Démarrage de la conversation ===
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
    context.user_data['sexe'] = update.message.text
    marques = sorted(set(row['marque'] for row in watch_db))
    keyboard = [marques[i:i+2] for i in range(0, len(marques), 2)]
    await update.message.reply_text("⌚ Marque ?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return MARQUE

async def get_marque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    marque = update.message.text
    context.user_data['marque'] = marque
    gammes = sorted(set(row['gamme'] for row in watch_db if row['marque'] == marque))
    keyboard = [gammes[i:i+2] for i in range(0, len(gammes), 2)]
    await update.message.reply_text("📎 Gamme ?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return GAMME

async def get_gamme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gamme = update.message.text
    context.user_data['gamme'] = gamme
    marque = context.user_data['marque']
    finitions = sorted(set(row['finition'] for row in watch_db if row['marque'] == marque and row['gamme'] == gamme))
    keyboard = [finitions[i:i+2] for i in range(0, len(finitions), 2)]
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

    # Recherche du prix d’achat
    data = context.user_data
    prix_achat = next(
        (row['prix_achat'] for row in watch_db
         if row['marque'] == data['marque']
         and row['gamme'] == data['gamme']
         and row['finition'] == data['finition']),
        "??"
    )
    context.user_data['prix_achat'] = prix_achat

    # Résumé final
    resume = (
        f"✅ Résumé de la commande :\n"
        f"👤 Nom : {data['nom']}\n"
        f"📞 Téléphone : {data['tel']}\n"
        f"🏙️ Ville : {data['ville']}\n"
        f"📍 Adresse : {data['adresse']}\n"
        f"👥 Sexe : {data['sexe']}\n"
        f"⌚ Marque : {data['marque']}\n"
        f"📎 Gamme : {data['gamme']}\n"
        f"🎨 Finition : {data['finition']}\n"
        f"🎁 Boîte : {data['boite']}\n"
        f"💰 Vente : {data['prix_vente']} | Achat : {prix_achat}"
    )

    await update.message.reply_text(resume + "\n\n✅ Merci, la commande est enregistrée.")

    # Insertion dans la sheet
    append_to_leads(context.user_data)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Commande annulée.")
    return ConversationHandler.END

def main():
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
            GAMME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gamme)],
            FINITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_finition)],
            BOITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_boite)],
            PRIX_VENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_prix_vente)],
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

if __name__ == "__main__":
    main()
