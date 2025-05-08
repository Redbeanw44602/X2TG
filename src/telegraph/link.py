import re

from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.serve import store_forwarded_message

    reply_to = update.message.reply_to_message
    if reply_to:
        rest_id = None
        try:
            rest_id = int(re.search(r'/status/(\d+)', update.message.text)[1])
        except Exception:
            await update.message.reply_text('invalid tweet url.')
            return
        store_forwarded_message(rest_id, [reply_to])
        await update.message.reply_text('done.')
    else:
        await update.message.reply_text('please reply a message.')
