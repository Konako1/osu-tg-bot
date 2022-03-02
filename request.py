from asyncio import sleep, create_task
from pprint import pprint
from typing import Any, Iterator

import httpx
import config

BASE_URL = 'https://osu.ppy.sh/api/v2'


def api_build_url(fragment: str) -> str:
    return BASE_URL + '/' + fragment.lstrip('/')


class Request:
    def __init__(self, token: str):
        self._token = token
        self._session = httpx.AsyncClient()

    async def update_token(self, delay: int = 0) -> None:
        if delay:
            await sleep(delay)
        resp = await self._session.post('https://osu.ppy.sh/oauth/token', json={
            'client_id': config.CLIENT_ID,
            'client_secret': config.CLIENT_SECRET,
            'grant_type': 'client_credentials',
            'scope': 'public',
        })
        resp.raise_for_status()
        data = resp.json()
        self._token = data['access_token']
        create_task(self.update_token(data['expires_in'] - 60))

    async def api_request(
            self,
            http_method: str,
            method: str,
            params: dict[str, Any],
    ) -> Any:
        url = api_build_url(method)
        if http_method == 'GET':
            response = await self._session.get(
                url,
                headers={'Authorization': 'Bearer ' + self._token},
                params=params
            )
        else:
            raise NotImplementedError
        response.raise_for_status()
        return response.json()

    async def get_osu_file(
            self,
            map_id: int
    ) -> str:
        r = await self._session.get(f"https://osu.ppy.sh/osu/{map_id}")
        return r.text

    async def get_user_beatmap_score(
            self,
            beatmap_id: int,
            user_id: int,
    ) -> dict:
        return await self.api_request(
            'GET',
            '/beatmaps/{beatmap}/scores/users/{user}'.format(beatmap=beatmap_id, user=user_id),
            {}
        )

    async def get_user_score(
            self,
            user_id: int,
            score_type: str,
            limit: int,
    ) -> list[dict]:
        return await self.api_request(
            'GET',
            '/users/{user}/scores/{type}'.format(user=user_id, type=score_type),
            {'limit': limit, 'include_fails': 1}
        )

    async def get_beatmap(
            self,
            beatmap_id: int,
    ) -> dict:
        return await self.api_request(
            'GET',
            '/beatmaps/{beatmap}'.format(beatmap=beatmap_id),
            {}
        )

    async def get_user_data(
            self,
            user_id: int,
    ) -> dict:
        return await self.api_request(
            'GET',
            '/users/{user}'.format(user=user_id),
            {}
        )

    async def get_user_id(
            self,
            username: str
    ) -> int:
        is_in_api = await self.api_request(
            'GET',
            '/search',
            {'query': username, 'mode': 'user', 'page': 0}
        )

        try:
            response = is_in_api['user']['data'][0]
        except IndexError:
            return 0
        return response['id']

    async def get_status_code(
            self,
            url: str
    ) -> int:
        response = await self._session.head(url)
        return response.status_code

    async def get_pic_as_bytes(
            self,
            url: str
    ) -> bytes:
        response = await self._session.get(url)
        return response.content


async def create_request():
    request = Request('')
    await request.update_token()
    return request
