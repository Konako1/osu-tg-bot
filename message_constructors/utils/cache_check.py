from datetime import datetime
from io import BytesIO, StringIO
from typing import Optional, Iterable, Iterator, TextIO

from PIL import Image

from api_model.beatmap import BeatmapData
from db import Db
from request import Request


async def _get_osu_id(username: str, db: Db, request: Request) -> Optional[int]:
    osu_id = await db.get_cached_osu_id_by_username(username)
    if osu_id is None:
        osu_id = await request.get_user_id(username)
        if osu_id == 0:
            return osu_id
        await db.cache_osu_user(username, osu_id)
    return osu_id


async def get_osu_id_by_username(username: str, db: Db, request: Request, tg_user_id: int) -> Optional[int]:
    if username is not None:
        username = username.lower()
        return await _get_osu_id(username, db, request)
    return await db.get_cached_osu_id_by_tg_id(tg_user_id)


async def bind_osu_id_with_tg_id(username: str, db: Db, request: Request, tg_user_id: int) -> bool:
    """
    Binds osu user id by username with tg user id. Returns `True` if cached, otherwise `False`.
    """
    username = username.lower()
    osu_id = await _get_osu_id(username, db, request)
    if osu_id is None or osu_id == 0:
        return False
    await db.cache_tg_user(tg_user_id, osu_id)
    return True


async def get_score_position(score_id: int, user_id: int, beatmap_id: int, db: Db, request: Request) -> int:
    position = None
    if score_id is not None:
        position = await db.get_user_score_position(score_id)
        if position is None:
            raw_submitted_user_beatmap_score = await request.get_user_beatmap_score(beatmap_id, user_id)
            submitted_score_id = raw_submitted_user_beatmap_score['score']['id']
            actual_position = raw_submitted_user_beatmap_score['position'] \
                if submitted_score_id == score_id \
                else None
            if actual_position != position:
                await db.cache_user_score_position(submitted_score_id, actual_position)
            position = actual_position
    return position


async def get_beatmap_data(beatmap_id: int, actual_last_updated: datetime, db: Db, request: Request) -> BeatmapData:
    saved_beatmap_data, saved_last_updated = None, None
    result = await db.get_beatmap_data(beatmap_id)
    if result is not None:
        saved_beatmap_data, saved_last_updated = result
    if saved_beatmap_data is None or actual_last_updated != saved_last_updated:
        raw_beatmap_data = await request.get_beatmap(beatmap_id)
        beatmap_data = BeatmapData.parse_obj(raw_beatmap_data)
        await db.cache_beatmap_data(beatmap_id, beatmap_data.json(by_alias=True), actual_last_updated)
    else:
        beatmap_data = BeatmapData.parse_raw(saved_beatmap_data)
    return beatmap_data


def get_saved_pic(path: str, osu_id: int) -> Optional[Image.Image]:
    """
    Tries to get an Image from path.

    :param path: Path, where image should be.
    :param osu_id: For osu map cover - "map_bg_cover". For osu user pfp - "user_pfp".
    :return: PIL.Image.Image. If image is not found, returns None.
    """
    try:
        img: Image.Image = Image.open(f'images/cache/{path}/{osu_id}.png')
    except FileNotFoundError:
        return None
    return img


def save_pic(path: str, osu_id: int, byte_cover: bytes) -> Image.Image:
    """
    Saves an Image.

    :param path: Path, where image should be. For osu map cover - "map_bg_cover". For osu user pfp - "user_pfp".
    :param osu_id: Osu map id or user id. Basically the name of the file.
    :param byte_cover: Byte representation of the Image.
    :return: Saved image as PIL.Image.Image.
    """
    bg = BytesIO(byte_cover)
    img: Image.Image = Image.open(bg)
    img.save(f'images/cache/{path}/{osu_id}.png')
    return img


async def get_osu_file(beatmap_id: int, last_updated: datetime, request: Request) -> TextIO:
    file_path = f'beatmap_files/osu_file/{beatmap_id}_{int(last_updated.timestamp())}.osu'
    try:
        osu_file = open(file_path, encoding='UTF-8')
    except FileNotFoundError:
        osu_file = await request.get_osu_file(beatmap_id)
        with open(file_path, 'w', encoding='UTF-8') as f:
            f.write(osu_file)
        osu_file = open(file_path, encoding='UTF-8')
    return osu_file
