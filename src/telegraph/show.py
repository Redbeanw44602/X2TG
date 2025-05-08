from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import app.serve as service

    draft = str()
    draft += f'Status: {service.status["event"]}'
    if service.status['event'] == 'Resting':
        until_time: datetime = service.status['data']
        draft += f' ({int((until_time - datetime.now()).total_seconds())} seconds left)'
    draft += '\n'
    draft += f'Forwarded: {len(service.data)}\n'
    await update.message.reply_text(draft.strip())
