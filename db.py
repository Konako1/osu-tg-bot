from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import asyncpg


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

    async def save_command_stat(self, message_date: datetime, command: str, tg_user_id: int) -> None:
        """
        Saves command info for statistics.

        :param message_date: Message date. Datetime with timezone.
        :param command: Bot commands as text. Available commands - "recent", "profile", "top5", "remember_me".
        :param tg_user_id: Telegram user id.
        """
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            await conn.execute('INSERT INTO stat(date, command, tg_user_id) '
                               'VALUES ($1, $2, $3)',
                               message_date, command.lower(), tg_user_id)

    async def get_all_stat(self, date: datetime = None) -> list[CommandStat]:
        """
        Message date, command and telegram user id for given day sa CommandStat dataclass. Returns all statistics if day is not given.
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
                                                                ")=$1",
                                                                date.day)
        stat_list: list[CommandStat] = []
        for record in result:
            stat_list.append(CommandStat(record[0], record[1], record[2]))
        return stat_list

    async def get_all_tg_id(self) -> list[int]:
        async with self._pool.acquire() as conn:  # type: asyncpg.Connection
            list_id = []
            result = await conn.fetch('SELECT tg_id FROM remembered_users')
            for tg_id in result:
                list_id.append(tg_id[0])
            return list_id
