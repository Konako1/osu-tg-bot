import time
from datetime import datetime
from pprint import pprint
from typing import Optional, Iterator

from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message, FSInputFile
from httpx import ReadTimeout
from httpx import HTTPStatusError

from api_model.beatmap import BeatmapData
from api_model.user_data import UserData
from db import Db
from message_constructors.recent_constructor import recent_message_constructor
from message_constructors.utils.cache_check import get_osu_id_by_username, get_osu_file
from message_constructors.utils.class_constructor import create_user_data_class, get_scores, create_score_class
from model.score import Score
from request import Request
from api_model.base_score import BaseScore

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
        user_data = await create_user_data_class(user_id, request)
    except ReadTimeout:
        return message.reply('Bancho is dead.')
    except HTTPStatusError as e:
        if e.response.status_code // 100 == 5:
            return message.reply('Bancho is dead.')
        raise
    except TypeError:
        return message.reply('User is quit w (no recent scores for past 24 hours).')
    osu_file = await get_osu_file(score.beatmap.id, score.beatmap.last_updated, request)
    photo = score.beatmapset.cover
    msg = recent_message_constructor(score, user_data, message.date, osu_file)
    osu_file.close()
    if await request.get_status_code(photo) >= 300:
        photo = FSInputFile('images/osu_bg.png')
    await message.reply_photo(photo, msg)
    await db.save_command_stat(message.date, 'recent', message.from_user.id)
