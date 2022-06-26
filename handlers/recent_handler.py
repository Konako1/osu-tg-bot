from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message, FSInputFile, CallbackQuery
from httpx import HTTPStatusError
from httpx import ReadTimeout

from db import Db
from message_constructors.recent_constructor import recent_message_constructor, create_stat_button, \
    recent_message_stat_constructor, Stat
from message_constructors.utils.cache_check import get_osu_id_by_username, get_osu_file
from message_constructors.utils.class_constructor import create_user_data_class, get_scores, create_score_class
from request import Request

router = Router()


@router.message(commands=['recent'])
async def recent(message: Message, request: Request, db: Db, command: CommandObject, bot: Bot):
    await bot.send_chat_action(message.chat.id, 'upload_voice')
    username = command.args
    user_id = await get_osu_id_by_username(username, db, request, message.from_user.id)
    if user_id is None:
        return message.reply('You forgot to write a username.\n'
                             '/remember_me to use that command without writing username.')
    if user_id == 0:
        return message.reply('User not found.')

    try:
        scores = await get_scores(user_id, request, 'recent', 1)
        score = await create_score_class(scores[0], request, db)
        osu_file = await get_osu_file(score.beatmap.id, score.beatmap.last_updated, request)
        user_data = await create_user_data_class(user_id, request)
    except ReadTimeout:
        return message.reply('Bancho is dead.')
    except HTTPStatusError as e:
        if e.response.status_code // 100 == 5:
            return message.reply('Bancho is dead.')
        raise
    except TypeError:
        return message.reply('User is quit w (no recent scores for past 24 hours).')

    photo = score.beatmapset.cover
    if await request.get_status_code(photo) >= 300:
        photo = FSInputFile('images/osu_bg.png')

    score_msg = recent_message_constructor(score, user_data, message.date, osu_file)
    osu_file.seek(0)
    stat_msg = recent_message_stat_constructor(score, osu_file)
    score_id = await db.add_score_stat(score_msg, stat_msg)
    button = create_stat_button(score_id, 'Statistics', False)
    await message.reply_photo(photo, score_msg, reply_markup=button)
    await db.save_command_stat(message.date, 'recent', message.from_user.id)

    osu_file.close()


@router.callback_query(Stat.filter())
async def change_page(query: CallbackQuery, db: Db, callback_data: Stat):
    await query.answer()
    score_id = callback_data.score_id
    is_stat = callback_data.is_stat
    button_text = 'Statistics' if is_stat else 'Score'
    result = await db.get_score_stat(not is_stat, score_id)
    await query.message.edit_caption(result, reply_markup=create_stat_button(score_id, button_text, not is_stat))
