from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

import asyncpg


@dataclass
class BeatmapData:
    music_id: int
    beatmap_id: int
    file_id: str
    title: str
    artist: str
    mapper: str
    length: int
    tags: Optional[str] = None


@dataclass
class MusicData:
    music_id: int
    file_id: str
    title: str
    artist: str
    length: int


@dataclass
class CommandStat:
    date: datetime
    command: str
    tg_user_id: int


class Db:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def close(self):
        await self._pool.close()

    @classmethod
    async def connect(cls, user: str, password: str, host: str, db: str):
        return cls(await asyncpg.create_pool(f'postgresql://{user}:{password}@{host}/{db}'))

    async def cache_tg_user(self, tg_id: int, osu_id: int) -> None:
        """
        Binds telegram id with osu id.

        Use only if there is no telegram id saved yet.

        :param tg_id: telegram user id.
        :param osu_id: osu user id.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO remembered_users(tg_id, osu_id) '
                               'VALUES ($1, $2) '
                               'ON CONFLICT(tg_id) DO UPDATE SET osu_id=$2',
                               tg_id, osu_id)

    async def remove_user_from_remember_me(self, tg_user_id: int) -> None:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('DELETE FROM remembered_users '
                               'WHERE tg_id=$1',
                               tg_user_id)

    async def get_cached_osu_id_by_tg_id(self, tg_id: int) -> Optional[int]:
        """Returns osu user id. Returns None if no id saved."""
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            return await conn.fetchval('SELECT osu_id '
                                       'FROM remembered_users '
                                       'WHERE tg_id=$1',
                                       tg_id)

    async def cache_osu_user(self, username: str, osu_id: int) -> None:
        """
        Binds osu username with osu user id.

        Use only if there is no osu user id saved yet.

        :param username: osu username.
        :param osu_id: osu user id.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO osu_users(osu_id, username) '
                               'VALUES ($1, $2)'
                               'ON CONFLICT(osu_id) DO UPDATE SET username=$2',
                               osu_id, username)

    async def get_cached_osu_id_by_username(self, username: str) -> Optional[int]:
        """Return osu user id. Returns None if no id saved."""
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            return await conn.fetchval('SELECT osu_id '
                                       'FROM osu_users '
                                       'WHERE username=$1',
                                       username)

    async def cache_beatmap_data(self, map_id: int, beatmap_data: str, last_updated: datetime) -> None:
        """
        Saves beatmap data by beatmap id.

        :param map_id: Osu beatmap id.
        :param beatmap_data: Osu beatmap data.
        :param last_updated: Beatmap last updated datetime.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO beatmap_data(map_id, data, last_updated) '
                               'VALUES ($1, $2, $3)',
                               map_id, beatmap_data, last_updated)

    async def get_beatmap_data(self, map_id: int) -> Optional[tuple[str, datetime]]:
        """
        Returns tuple of osu beatmap data as json str and last updated datetime. None if no data saved.

        :param map_id: Osu map id.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            record: asyncpg.Record = await conn.fetchrow('SELECT data, last_updated '
                                                         'FROM beatmap_data '
                                                         'WHERE map_id=$1',
                                                         map_id)
        if record is None:
            return None
        return record[0], record[1]

    async def cache_user_score_position(self, score_id: int, position: int) -> None:
        """
        Saves user's position on a map by score id.

        :param score_id: Osu score id.
        :param position: User's position on a map.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO score_positions(score_id, position) '
                               'VALUES ($1, $2) ON CONFLICT(score_id) DO UPDATE SET position=$2',
                               score_id, position)

    async def get_user_score_position(self, score_id: int) -> Optional[int]:
        """Returns user's position on a map by score id."""
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            return await conn.fetchval('SELECT position '
                                       'FROM score_positions '
                                       'WHERE score_id=$1',
                                       score_id)

    async def add_score_stat(self, score: str, stat: str, is_stat: bool = False) -> int:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            return await conn.fetchval('INSERT INTO score_stat (score, stat, is_stat) '
                                       'VALUES ($1, $2, $3) '
                                       'RETURNING id',
                                       score, stat, is_stat)

    async def get_score_stat(self, is_stat: bool, score_id: int) -> str:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            return await conn.fetchval('UPDATE score_stat '
                                       'SET is_stat=$1 '
                                       'WHERE id=$2 '
                                       'RETURNING '
                                       'CASE WHEN $1 = FALSE THEN score '
                                       'ELSE stat '
                                       'END',
                                       is_stat, score_id)

    async def find_music(self, value: str, cursor: int) -> list[MusicData]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            result: list[asyncpg.Record] = await conn.fetch("SELECT music.id, file_id, artist, title, length "
                                                            "FROM music "
                                                            "JOIN music_mappers msm "
                                                            "ON music.id = msm.music_id "
                                                            "JOIN mappers m "
                                                            "ON m.id = msm.mapper_id "
                                                            f"WHERE music.artist || "
                                                            f"' ' || music.title || "
                                                            f"' ' || m.mapper "
                                                            f"ILIKE $1 "
                                                            f"OFFSET $2 "
                                                            f"LIMIT 11",
                                                            f"%{value}%", cursor*10)
            music: list[MusicData] = []
            for music_data in result:
                music.append(MusicData(
                    music_id=music_data[0],
                    file_id=music_data[1],
                    artist=music_data[2],
                    title=music_data[3],
                    length=music_data[4],
                ))
            return music

    async def find_music_by_file_id(self, file_id: str) -> Optional[MusicData]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            result: list[asyncpg.Record] = await conn.fetch("SELECT id, file_id, artist, title, length "
                                                            "FROM music "
                                                            "WHERE file_id=$1",
                                                            file_id)
            if not result:
                return None
            return MusicData(
                music_id=result[0],
                file_id=result[1],
                artist=result[2],
                title=result[3],
                length=result[4],)

    async def find_music_by_beatmap_id(self, beatmap_id: int) -> Optional[list[BeatmapData]]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            result: asyncpg.Record = await conn.fetch("SELECT file_id, artist, title, length, m.mapper, music.id "
                                                      "FROM music "
                                                      "JOIN music_mappers mm "
                                                      "ON mm.music_id = music.id "
                                                      "JOIN mappers m "
                                                      "ON m.id = mm.mapper_id "
                                                      "WHERE m.beatmap_id=$1",
                                                      beatmap_id)
            if not result:
                return None
            beatmap_datas = []
            for data in result:
                beatmap_datas.append(BeatmapData(
                    music_id=data[5],
                    beatmap_id=beatmap_id,
                    file_id=data[0],
                    artist=data[1],
                    title=data[2],
                    length=data[3],
                    mapper=data[4]))
            return beatmap_datas

    async def find_beatmaps_by_music_id(self, music_id: int) -> tuple[list[str], list[int]]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            result: list[asyncpg.Record] = await conn.fetch('SELECT mapper, beatmap_id '
                                                            'FROM mappers '
                                                            'JOIN music_mappers mm '
                                                            'ON mappers.id = mm.mapper_id '
                                                            'WHERE music_id=$1',
                                                            music_id)
            mappers = []
            beatmap_ids = []
            for mapper, beatmap_id in result:
                mappers.append(mapper)
                beatmap_ids.append(beatmap_id)
            return mappers, beatmap_ids

    async def get_id_by_token(self, word: str) -> list[str]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            result: list[asyncpg.Record] = await conn.fetch('SELECT file_id '
                                                            'FROM music_tokens '
                                                            'WHERE word=$1',
                                                            word)
            id_list: list[str] = []
            for file_id in result:
                id_list.append(file_id[0])
            return id_list

    async def get_file_id_by_music_id(self, music_id: int) -> str:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            return await conn.fetchval('SELECT file_id '
                                       'FROM music '
                                       'WHERE id=$1',
                                       music_id)

    async def save_command_stat(self, message_date: datetime, command: str, tg_user_id: int) -> None:
        """
        Saves command info for statistics.

        :param message_date: Message date. Datetime with timezone.
        :param command: Bot commands as text. Available commands - "recent", "profile", "top5", "remember_me", "track".
        :param tg_user_id: Telegram user id.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO stat(date, command, tg_user_id) '
                               'VALUES ($1, $2, $3)',
                               message_date, command.lower(), tg_user_id)

    async def get_all_stat(self, date: datetime = None) -> list[CommandStat]:
        """
        Returns message date, command and telegram user id for given day sa CommandStat dataclass. Returns all statistics if day is not given.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            if date is None:
                result: list[asyncpg.Record] = await conn.fetch("SELECT date, command, tg_user_id "
                                                                "FROM stat")
            else:
                result: list[asyncpg.Record] = await conn.fetch("SELECT date, command, tg_user_id "
                                                                "FROM stat "
                                                                "WHERE EXTRACT("
                                                                "DAY FROM date "
                                                                "AT TIME ZONE 'Asia/Yekaterinburg'"
                                                                ")=$1 "
                                                                "AND EXTRACT("
                                                                "MONTH FROM date "
                                                                "AT TIME ZONE 'Asia/Yekaterinburg'"
                                                                ")=$2 "
                                                                "AND EXTRACT("
                                                                "YEAR FROM date "
                                                                "AT TIME ZONE 'Asia/Yekaterinburg'"
                                                                ")=$3",
                                                                date.day, date.month, date.year)
        stat_list: list[CommandStat] = []
        for record in result:
            stat_list.append(CommandStat(record[0], record[1], record[2]))
        return stat_list

    async def save_music(self, file_id: str, artist: str, title: str, length: int, is_tv_size: bool, is_bpm_changed: bool) -> Optional[int]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            music_id = await conn.fetchval('SELECT id FROM music '
                                               'WHERE artist=$1 AND title=$2 AND length=$3',
                                               artist, title, length)
            if music_id is not None:
                return int(music_id)
            return int(await conn.fetchval('INSERT INTO music(file_id, artist, title, length, is_tv_size, is_bpm_changed) '
                                           'VALUES ($1, $2, $3, $4, $5, $6) '
                                           'ON CONFLICT (artist, title, length, file_id) DO NOTHING '
                                           'RETURNING id',
                                           file_id, artist, title, length, is_tv_size, is_bpm_changed))

    async def save_mapper(self, mapper: str, beatmap_id: int) -> int:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            mapper_id = await conn.fetchval('SELECT id FROM mappers '
                                                'WHERE mapper=$1 AND beatmap_id=$2',
                                                mapper, beatmap_id)
            if mapper_id is not None:
                return int(mapper_id)
            return int(await conn.fetchval('INSERT INTO mappers(mapper, beatmap_id) '
                                           'VALUES ($1, $2) '
                                           'ON CONFLICT (mapper, beatmap_id) DO NOTHING '
                                           'RETURNING id',
                                           mapper, beatmap_id))

    async def save_music_mapper(self, music_id: int, mapper_id: int):
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO music_mappers(music_id, mapper_id) '
                               'VALUES ($1, $2) '
                               'ON CONFLICT (mapper_id, music_id) DO NOTHING ',
                               music_id, mapper_id)

    async def is_music_saved(self, artist: str, title: str, length: float) -> Union[tuple[list[int], str, int], None]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            result: list[asyncpg.Record] = await conn.fetch('SELECT file_id, beatmap_id, music.id FROM music '
                                                            'JOIN music_mappers msm '
                                                            'ON music.id = msm.music_id '
                                                            'JOIN mappers m '
                                                            'ON m.id = msm.mapper_id '
                                                            'WHERE artist=$1 '
                                                            'AND title=$2 '
                                                            'AND length=$3',
                                                            artist, title, length)
            beatmap_id_list = []
            file_id = None
            music_id = None
            for data in result:
                file_id = data[0]
                beatmap_id_list.append(data[1])
                music_id = data[2]
            return beatmap_id_list, file_id, music_id

    async def add_music_token(self, word: str, file_id: str):
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO music_tokens(word, file_id) '
                               'VALUES ($1, $2) '
                               'ON CONFLICT DO NOTHING',
                               word, file_id)

    async def get_all_search_music_data(self) -> list[BeatmapData]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            result: list[asyncpg.Record] = await conn.fetch('SELECT m.beatmap_id, file_id, artist, title, length, m.mapper, music.id '
                                                            'FROM music '
                                                            'JOIN music_mappers msm '
                                                            'ON music.id = msm.music_id '
                                                            'JOIN mappers m '
                                                            'ON m.id = msm.mapper_id ')
            music_data_list: list[BeatmapData] = []
            for data in result:
                music_data_list.append(BeatmapData(
                    beatmap_id=data[0],
                    file_id=data[1],
                    artist=data[2],
                    title=data[3],
                    length=data[4],
                    mapper=data[5],
                    music_id=data[6]
                ))
            return music_data_list

    async def get_all_tg_id(self) -> list[int]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            list_id = []
            result = await conn.fetch('SELECT tg_id FROM remembered_users')
            for tg_id in result:
                list_id.append(tg_id[0])
            return list_id
