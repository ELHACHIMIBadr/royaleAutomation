import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
import gspread
from google.oauth2.service_account import Credentials

# === Logger ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# === Environ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8443))

# === Google Sheets Auth ===
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file("royaleheurebot-43c46ef6f78f.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Commande Royale Heure")
leads_ws = sheet.worksheet("Leads")
db_ws = sheet.worksheet("Base de données montres RH")

# === States ===
(
    NOM, TEL, VILLE, ADRESSE, SEXE,
    MARQUE, GAMME, FINITION, BOITE, PRIX_VENTE, RESUME
) = range(11)

user_data_temp = {}

async def start_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in [5427202496, 1580306191, 1122334455]:
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
    marques = list(set([row[0] for row in db_ws.get_all_values()[1:] if row[0]]))
    await update.message.reply_text("⌚ Marque ?", reply_markup=ReplyKeyboardMarkup([marques[i:i+2] for i in range(0, len(marques), 2)], one_time_keyboard=True))
    return MARQUE

async def get_marque(update: Update, context: ContextTypes.DEFAULT_TYPE):
    marque = update.message.text
    context.user_data['marque'] = marque
    gammes = list(set([row[1] for row in db_ws.get_all_values()[1:] if row[0] == marque]))
    await update.message.reply_text("📎 Gamme ?", reply_markup=ReplyKeyboardMarkup([gammes[i:i+2] for i in range(0, len(gammes), 2)], one_time_keyboard=True))
    return GAMME

async def get_gamme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gamme = update.message.text
    context.user_data['gamme'] = gamme
    marque = context.user_data['marque']
    finitions = list(set([row[2] for row in db_ws.get_all_values()[1:] if row[0] == marque and row[1] == gamme]))
    await update.message.reply_text("🎨 Finition ?", reply_markup=ReplyKeyboardMarkup([finitions[i:i+2] for i in range(0, len(finitions), 2)], one_time_keyboard=True))
    return FINITION

async def get_finition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['finition'] = update.message.text
    await update.message.reply_text("🎁 Boîte ?", reply_markup=ReplyKeyboardMarkup([["Simple", "Originale"]], one_time_keyboard=True))
    return BOITE

async def get_boite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['boite'] = update.message.text
    await update.message.reply_text("💰 Prix de vente au client ?")
    return PRIX_VENTE

async def get_prix_vente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['prix_vente'] = update.message.text
    marque = context.user_data['marque']
    gamme = context.user_data['gamme']
    finition = context.user_data['finition']

    db_rows = db_ws.get_all_values()[1:]
    prix_achat = next((row[3] for row in db_rows if row[0] == marque and row[1] == gamme and row[2] == finition), "??")
    context.user_data['prix_achat'] = prix_achat

    resume = (
        f"✅ Résumé de la commande :\n"
        f"👤 Nom : {context.user_data['nom']}\n"
        f"📞 Téléphone : {context.user_data['tel']}\n"
        f"🏙️ Ville : {context.user_data['ville']}\n"
        f"📍 Adresse : {context.user_data['adresse']}\n"
        f"👥 Sexe : {context.user_data['sexe']}\n"
        f"⌚ Marque : {context.user_data['marque']}\n"
        f"📎 Gamme : {context.user_data['gamme']}\n"
        f"🎨 Finition : {context.user_data['finition']}\n"
        f"🎁 Boîte : {context.user_data['boite']}\n"
        f"💰 Vente : {context.user_data['prix_vente']} | Achat : {prix_achat}"
    )
    await update.message.reply_text(resume + "\n\nMerci, la commande est enregistrée.")

    leads_ws.append_row([
        "",  # Date auto dans Google Sheet
        context.user_data['nom'],
        context.user_data['tel'],
        context.user_data['ville'],
        "",  # coût de livraison à compléter
        context.user_data['marque'],
        context.user_data['gamme'],
        context.user_data['finition'],
        prix_achat,
        context.user_data['prix_vente'],
        "Confirmé",
        context.user_data['adresse'],
        ""  # commentaire
    ])
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
