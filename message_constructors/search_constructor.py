import re
from typing import Optional

from db import MusicData, Db
from message_constructors.utils.utils import get_id_list


async def search_constructor(args: str, cursor: int, db: Db) -> Optional[list[MusicData]]:
    id_pattern = r'https://osu\.ppy\.sh/beatmapsets/([0-9]+)*'
    match = re.match(id_pattern, args)
    if match is not None:
        song = await db.find_music_by_id(int(match[1]))
        return [song]

    music: list[MusicData] = []
    music.extend(await db.find_music(args, cursor))
    sorted_ids = await get_id_list(args, db)

    for i, beatmap_id in enumerate(sorted_ids):
        if i < cursor * 10:
            continue
        if len(music) > 10:
            break
        in_music = False
        for song in music:
            if beatmap_id == song.beatmap_id:
                in_music = True
        if not in_music:
            music.append(await db.find_music_by_id(beatmap_id))
    return music
