from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class Beatmap(BaseModel):
    id: int
    last_updated: datetime


class BeatmapData(BaseModel):
    od: Annotated[float, Field(alias='accuracy')]
    ar: float
    cs: float
    hp: Annotated[float, Field(alias='drain')]
    max_combo: int
    total_length: int
    stars: Annotated[float, Field(alias='difficulty_rating')]
    bpm: float
    count_circles: int
    count_sliders: int
    count_spinners: int
    status: str
    url: str
    difficulty_name: Annotated[str, Field(alias='version')]
    last_updated: datetime
