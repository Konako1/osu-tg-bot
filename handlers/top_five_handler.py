from io import BytesIO

from PIL import Image
from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message, BufferedInputFile
from httpx import ReadTimeout, HTTPStatusError

from db import Db
from message_constructors.top_five_constructor import top_five_message_constructor, thumbnail_maker
from message_constructors.utils.cache_check import get_osu_id_by_username
from message_constructors.utils.class_constructor import create_user_data_class, get_scores
from message_constructors.utils.utils import gather_requests, get_saved_image
from model.score import Score
from requests.osu_request import OsuRequest

router = Router()


@router.message(commands=['top5'])
async def top_five(message: Message, command: CommandObject, request: OsuRequest, db: Db, bot: Bot, ):
    await bot.send_chat_action(message.chat.id, 'upload_video')
    username = command.args
    user_id = await get_osu_id_by_username(username, db, request, message.from_user.id)
    if user_id is None:
        return message.reply('You forgot to write a username.\n'
                             '/remember_me to use that command without writing username.')
    if user_id == 0:
        return message.reply('User not found.')
    try:
        dict_scores = await get_scores(user_id, request, 'best', 5)
        scores: list[Score] = await gather_requests(dict_scores, 'score', request, db)
        images: list[Image.Image] = await gather_requests(scores, 'image', request, db)
        user_data = await create_user_data_class(user_id, request)
        star_ratings = await gather_requests(scores, 'sr', request, db)
    except ReadTimeout:
        return message.reply('Bancho is dead.')
    except HTTPStatusError as e:
        if e.response.status_code // 100 == 5:
            return message.reply('Bancho is dead.')
        raise
    except TypeError as e:
        return message.reply("User hasn't set any scores yet.")

    if len(images) == 5:
        thumbnail = thumbnail_maker(images)
    else:  # dumb situation fix when user have less than 5 scores
        bg = await get_saved_image(scores[0].beatmap.id, scores[0].beatmapset.cover, request)
        thumbnail = BytesIO()
        bg.save(thumbnail, 'png')
    thumbnail.seek(0)

    msg = top_five_message_constructor(scores, user_data, star_ratings)
    await message.reply_photo(BufferedInputFile(thumbnail.read(), "file.png"), msg)
    await db.save_command_stat(message.date, 'top5', message.from_user.id)
