import re
from typing import Optional, Union

from db import BeatmapData, Db, MusicData
from message_constructors.utils.utils import get_id_list


async def search_constructor(args: str, cursor: int, db: Db) -> Union[list[BeatmapData], list[MusicData], None]:
    match = re.match(r'https://osu\.ppy\.sh/beatmapsets/([0-9]+)*', args)
    if match is not None:
        songs = await db.find_music_by_beatmap_id(int(match[1]))
        return songs

    music: list[MusicData] = []
    music.extend(await db.find_music(args, cursor))
    sorted_ids = await get_id_list(args, db)

    for i, file_id in enumerate(sorted_ids):
        if i < cursor * 10:
            continue
        if len(music) > 10:
            break
        in_music = False
        for song in music:
            if file_id == song.file_id:
                in_music = True
        if not in_music:
            music.append(await db.find_music_by_file_id(file_id))
    return music
