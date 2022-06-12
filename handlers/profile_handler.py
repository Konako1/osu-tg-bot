from pprint import pprint
from typing import Optional

from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message, FSInputFile
from httpx import ReadTimeout, HTTPStatusError

from db import Db
from message_constructors.utils.class_constructor import create_user_data_class, get_scores, create_score_class
from message_constructors.profile_constructor import profile_message_constructor
from request import Request
from message_constructors.utils.cache_check import get_osu_id_by_username, get_osu_file

router = Router()


@router.message(commands=['profile'])
async def profile(message: Message, request: Request, db: Db, bot: Bot, command: CommandObject):
    await bot.send_chat_action(message.chat.id, 'record_voice')
    username = command.args
    user_id = await get_osu_id_by_username(username, db, request, message.from_user.id)
    if user_id is None:
        return message.reply('You forgot to write a username.\n'
                             '/remember_me to use that command without writing username.')
    if user_id == 0:
        return message.reply('User not found.')

    try:
        user_data = await create_user_data_class(user_id, request)
        scores = await get_scores(user_id, request, 'best', 1)
        score = await create_score_class(scores[0], request, db)
        star_rating = await request.get_star_rating(score.beatmap.id, score.mods, score.mode_int)
    except ReadTimeout:
        return message.reply('Bancho is dead.')
    except HTTPStatusError as e:
        if e.response.status_code // 100 == 5:
            return message.reply('Bancho is dead.')
        raise
    except TypeError as e:
        return message.reply("User hasn't set any scores yet.")

    photo = user_data.avatar_url
    if await request.get_status_code(photo) >= 300:
        photo = FSInputFile('images/default_user_avatar.png')

    msg = profile_message_constructor(user_data, score, star_rating)
    await message.reply_photo(photo, msg)
    await db.save_command_stat(message.date, 'profile', message.from_user.id)
