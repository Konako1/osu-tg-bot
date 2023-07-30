from asyncio import sleep, create_task
from typing import Any, Optional, Union

import httpx
import config

BASE_URL = config.OSU_TOOLS_API.lstrip('/')


def api_build_url(fragment: str) -> str:
    return BASE_URL + '/' + fragment.lstrip('/')


class OsuToolsRequest:
    def __init__(self):
        self._session = httpx.AsyncClient()

    async def api_request(
            self,
            method: str,
            params: Optional[dict[str, Any]] = None,
    ) -> Any:
        response = await self._session.get(
            api_build_url(method),
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def play_performance(
            self,
            beatmap_id: int,
            combo: int,
            mod: list[str],
            misses: int,
            goods: int,
            mehs: int,
    ) -> dict:
        return await self.api_request(
            '/performance/{beatmap}'.format(beatmap=beatmap_id),
            {
                'combo': combo,
                'mod': mod,
                'misses': misses,
                'goods': goods,
                'mehs': mehs,
            }
        )

    async def play_performance_if_fc(
            self,
            beatmap_id: int,
            mod: list[str],
            goods: int,
            mehs: int,
    ) -> dict:
        return await self.api_request(
            '/performance/{beatmap}'.format(beatmap=beatmap_id),
            {
                'mod': mod,
                'goods': goods,
                'mehs': mehs,
            }
        )

    async def play_performance_if_ss(
            self,
            beatmap_id: int,
            mod: list[str],
    ) -> dict:
        return await self.api_request(
            '/performance/{beatmap}'.format(beatmap=beatmap_id),
            {
                'mod': mod,
            }
        )


async def create_request():
    request = OsuToolsRequest()
    return request
