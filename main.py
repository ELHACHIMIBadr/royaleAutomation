import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

import os

# Afficher les logs dans Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # À définir dans les variables d’environnement Render

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"[LOG] Message reçu : {user_message}")  # Ce message apparaîtra dans les logs Render

    await update.message.reply_text("✅ Message reçu, test réussi !")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handler de tout message texte
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Bot lancé...")
    app.run_polling()

if __name__ == '__main__':
    main()
