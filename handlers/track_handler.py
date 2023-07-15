import asyncio
from asyncio import create_task, sleep
from dataclasses import dataclass
from datetime import datetime, timezone
from pprint import pprint
from typing import Optional, TextIO, Union

from PIL import Image
from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message, FSInputFile
from httpx import ReadTimeout, HTTPStatusError
from pydantic.typing import NoneType

from api_model.user_data import UserData
from db import Db, TrackingInfo
from message_constructors.recent_constructor import recent_message_constructor
from message_constructors.utils.class_constructor import get_scores, create_score_class, create_user_data_class
from message_constructors.utils.utils import gather_requests
from model.score import Score
from request import Request
from message_constructors.utils.cache_check import get_osu_id_by_username, get_osu_file

router = Router()


@dataclass
class ScoreMessageInfo:
    score: Score
    osu_file: TextIO
    image: Union[str, FSInputFile]
    user_data: UserData


# def apply_filters(filters: str, score: Score) -> bool:


async def track_scores(db: Db, request: Request, bot: Bot):
    while True:
        tracking_list: list[TrackingInfo] = await db.get_all_users_tracking_info()

        users = []
        user_data_requests = []
        dict_score_requests = []
        for track in tracking_list:
            if track.user_id not in users:
                users.append(track.user_id)
                dict_score_requests.append(get_scores(track.user_id, request, 'recent', 1))
                user_data_requests.append(create_user_data_class(track.user_id, request))

        try:
            dict_scores_raw = await asyncio.gather(*dict_score_requests)
            user_data_raw = await asyncio.gather(*user_data_requests)
        except ReadTimeout as e:
            continue
        except HTTPStatusError as e:
            continue

        dict_scores: list[Optional[dict]] = []
        for score_dict in dict_scores_raw:
            try:
                dict_scores.append(score_dict[0])
            except TypeError:
                dict_scores.append(None)

        filtered_dict_scores: list[dict] = []
        filtered_user_data: list[UserData] = []
        for track in tracking_list:
            for k, score_dict in enumerate(dict_scores):
                if score_dict is not None \
                        and track.user_id == score_dict['user']['id'] \
                        and score_dict not in filtered_dict_scores \
                        and (score_dict['id'] != track.score_id or track.score_id == 0):
                    # TODO: insert filters here
                    filtered_dict_scores.append(score_dict)
                    filtered_user_data.append(user_data_raw[k])

        if not filtered_dict_scores:
            await asyncio.sleep(5.0)
            continue

        scores: list[Score] = await gather_requests(filtered_dict_scores, 'score', request, db)
        photos: list[Union[str, FSInputFile]] = [score.beatmapset.cover for score in scores]
        osu_files: list[TextIO] = await gather_requests(scores, 'osu_file', request, db)
        status_codes: list[int] = await gather_requests(photos, 'status_code', request, db)
        user_data_list: list[UserData] = [item for item in filtered_user_data]

        for j, status_code in enumerate(status_codes):
            if status_code >= 300:
                photos[j] = FSInputFile('images/osu_bg.png')

        score_messages: list[tuple[TrackingInfo, ScoreMessageInfo]] = []
        for track in tracking_list:
            for i in range(len(scores)):
                if track.user_id == scores[i].user_id:
                    score_messages.append((track, ScoreMessageInfo(
                        scores[i],
                        osu_files[i],
                        photos[i],
                        user_data_list[i])))

        for track, score_info in score_messages:
            msg = recent_message_constructor(score_info.score, score_info.user_data, datetime.utcnow().replace(tzinfo=timezone.utc), score_info.osu_file)
            await bot.send_photo(track.chat_id, score_info.image, msg)
            await db.update_score_tracking(track.chat_id, track.user_id, track.filter, score_info.score.id)
            await asyncio.sleep(5/len(score_messages))


@router.message(commands=['track'])
async def track_handler(message: Message, request: Request, db: Db, command: CommandObject):
    username = command.args
    if username is None:
        return message.reply('You forgot to write a username for tracking.')

    user_id = await get_osu_id_by_username(username, db, request, message.from_user.id)
    if user_id == 0:
        return message.reply('User not found')

    result = await db.get_tracking_info(message.chat.id, user_id)
    if result is None:
        await db.update_score_tracking(message.chat.id, user_id, 'all', 0)  # NEED TO FIX all
        await message.reply(f"{username}'s scores began to be tracked!")
        await db.save_command_stat(message.date, 'track', message.from_user.id)
        return
    return message.reply(f'{username} already being tracked')
