from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from api_model.beatmapset import Beatmapset
from api_model.beatmap import Beatmap


class Statistics(BaseModel):
    count_300: int
    count_100: int
    count_50: int
    count_miss: int


class BaseScore(BaseModel):
    accuracy: float
    beatmap: Beatmap
    beatmapset: Beatmapset
    best_id: Optional[int]
    created_at: datetime
    id: Optional[int]
    max_combo: int
    mods: list[str]
    passed: bool
    perfect: bool
    pp: Optional[float]
    rank: str
    score: int
    statistics: Statistics
    user_id: int
    mode_int: int
