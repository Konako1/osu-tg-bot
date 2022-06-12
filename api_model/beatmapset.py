from typing import Annotated

from pydantic import BaseModel, Field


class Beatmapset(BaseModel):
    id: int
    artist: str
    covers: dict
    title: str
    creator: str
    creator_id: Annotated[int, Field(alias='user_id')]

    @property
    def cover(self) -> str:
        return self.covers['cover']

    @property
    def square_cover(self):
        return self.covers['list@2x']

