from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pong = 'pong!\n'
    reply_to = update.message.reply_to_message
    if reply_to:
        pong += f'replied_message_id: {reply_to.message_id}\n'
    await update.message.reply_text(pong.strip())
