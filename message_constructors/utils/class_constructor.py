from pprint import pprint
from typing import Optional

from api_model.base_score import BaseScore
from api_model.beatmap import BeatmapData
from api_model.user_data import UserData
from db import Db
from message_constructors.utils.cache_check import get_score_position, get_beatmap_data
from model.score import Score
from request import Request


async def get_scores(user_id: int, request: Request, score_type: str, limit: int)\
        -> Optional[list[dict]]:
    scores = await request.get_user_score(user_id, score_type, limit)
    if not scores:
        return None
    return scores


async def create_score_class(score: dict, request: Request, db: Db) -> Score:
    base_score = BaseScore.parse_obj(score)
    beatmap_data = await get_beatmap_data(base_score.beatmap.id, base_score.beatmap.last_updated, db, request)
    position = await get_score_position(base_score.id, base_score.user_id, base_score.beatmap.id, request)
    return Score.parse_obj({**base_score.dict(by_alias=True), "beatmap_data": beatmap_data, "position": position})


async def create_user_data_class(user_id: int, request: Request) -> UserData:
    raw_user_data = await request.get_user_data(user_id)
    # pprint(raw_user_data)
    return UserData.parse_obj(raw_user_data)
