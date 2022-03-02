import os
import time
from typing import Any, Iterator, TextIO

from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message, FSInputFile, BufferedInputFile
from PIL import Image, ImageOps
from httpx import ReadTimeout, HTTPStatusError

from db import Db
from message_constructors.utils.class_constructor import create_user_data_class, get_scores, create_score_class
from message_constructors.top_five_constructor import top_five_message_constructor, thumbnail_maker
from message_constructors.utils.cache_check import get_osu_id_by_username, get_osu_file
from message_constructors.utils.utils import get_saved_image
from model.score import Score
from request import Request

router = Router()


@router.message(commands=['top5'])
async def top_five(message: Message, command: CommandObject, request: Request, db: Db, bot: Bot):
    await bot.send_chat_action(message.chat.id, 'upload_video')
    username = command.args
    user_id = await get_osu_id_by_username(username, db, request, message.from_user.id)
    if user_id is None:
        return message.reply('You forgot to write a username.\n'
                             '/remember_me to use that command without writing username.')
    if user_id == 0:
        return message.reply('User not found.')
    scores: list[Score] = []
    try:
        dict_scores = await get_scores(user_id, request, 'best', 5)
        for score in dict_scores:
            scores.append(await create_score_class(score, request, db))
        user_data = await create_user_data_class(user_id, request)
    except ReadTimeout:
        return message.reply('Bancho is dead.')
    except HTTPStatusError as e:
        if e.response.status_code // 100 == 5:
            return message.reply('Bancho is dead.')
        raise
    osu_files: list[TextIO] = []
    for score in scores:
        osu_files.append(await get_osu_file(score.beatmap.id, score.beatmap.last_updated, request))
    msg = top_five_message_constructor(scores, user_data, osu_files)
    for file in osu_files:
        file.close()
    images: list[Image.Image] = []
    pp_list: list[int] = []
    for score in scores:
        images.append(await get_saved_image(score.beatmap.id, score.beatmapset.square_cover, request))
        pp_list.append(int(score.pp))
    thumbnail = thumbnail_maker(images, pp_list)
    thumbnail.seek(0)

    await message.reply_photo(BufferedInputFile(thumbnail.read(), "file.png"), msg)
    await db.save_command_stat(message.date, 'top5', message.from_user.id)
