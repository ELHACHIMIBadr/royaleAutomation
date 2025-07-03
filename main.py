import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Configure logging for Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8443))  # Render assigns PORT dynamically
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Set this in Render's environment variables

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages and respond with 'Hello'."""
    user_message = update.message.text
    logger.info(f"Received message: {user_message}")
    await update.message.reply_text("Hello")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Optional start command for the bot."""
    await update.message.reply_text("Bot started! Send any message, and I'll reply with 'Hello'.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Main function to run the bot."""
    if not BOT_TOKEN or not WEBHOOK_URL:
        logger.error("BOT_TOKEN or WEBHOOK_URL not set in environment variables.")
        return

    # Build the application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    # Start the bot with webhook
    logger.info("Starting bot with webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,  # Secure the webhook endpoint
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()
