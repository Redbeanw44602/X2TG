from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from twitter.config import ENABLE_FXTWITTER, MAIN_URL, FXTWITTER_URL

import asyncio

can_fix_list = []
message = None


async def hanele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global can_fix_list, message
    import app.serve as service  # TODO: WIP

    message = await update.message.reply_text('rewinding all tweets...')
    await service._run_sync_all()

    unsynched_list = []
    for thread in service._timeline._all_threads:
        if str(thread.rest_id) not in service.data:
            unsynched_list.append(thread)
    if not unsynched_list:
        await message.edit_text('everything is fine now, no need to fix.')
        return

    latest_synched_thread_rest_id = None
    current_largest_msg_id = 0
    for rest_id, msg_ids in service.data.items():
        for msg_id in msg_ids:
            if msg_id > current_largest_msg_id:
                latest_synched_thread_rest_id = int(rest_id)
    if not latest_synched_thread_rest_id:
        await message.edit_text('unsupported.')
        return

    latest_synched_thread = None
    for thread in service._timeline._all_threads:
        if thread.rest_id == latest_synched_thread_rest_id:
            latest_synched_thread = thread
    can_fix_list = []
    for thread in unsynched_list[:]:
        if latest_synched_thread.date <= thread.date:
            can_fix_list.append(thread)
            unsynched_list.remove(thread)

    keyboard = (
        len(can_fix_list) > 0
        and InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                f'Resend {len(can_fix_list)} Tweets',
                callback_data='start_fix',
            )
        )
        or None
    )

    draft = f'A total of **{len(unsynched_list) + len(can_fix_list)}** tweets exist remotely but not in the current channel.\n'
    draft += f'\n❌ Inconsistent timelines ({len(unsynched_list)})\n'
    for thread in unsynched_list:
        draft += f'[{thread.rest_id}]({ENABLE_FXTWITTER and FXTWITTER_URL or MAIN_URL}/{service._username}/status/{thread.rest_id})\n'

    if can_fix_list:
        draft += f'\n✔️ Can be fixed ({len(can_fix_list)})\n'
        for thread in can_fix_list:
            draft += f'[{thread.rest_id}]({ENABLE_FXTWITTER and FXTWITTER_URL or MAIN_URL}/{service._username}/status/{thread.rest_id})\n'

    await message.edit_text(
        draft, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import app.serve as service

    query = update.callback_query
    await query.answer()

    if not query.data.startswith('start_fix'):  # TODO: auth
        return

    can_fix_list.sort(key=lambda x: x.date)
    for thread in can_fix_list:
        await service._timeline.trigger_add_thread(thread, True)
        await asyncio.sleep(4)

    await message.edit_text('all done!')
