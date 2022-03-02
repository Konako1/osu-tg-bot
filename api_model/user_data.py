from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field


class Statistics(BaseModel):
    country_rank: Optional[int]
    global_rank: Optional[int]
    hit_accuracy: float
    level_raw: Annotated[dict, Field(alias='level')]
    play_count: int
    play_time: int
    pp: float
    ranked_score: int
    total_score: int
    replays_watched_by_others: int

    @property
    def level(self):
        lvl = self.level_raw['current'] + self.level_raw['progress'] * 0.01
        return lvl


class UserData(BaseModel):
    id: int
    avatar_url: Optional[str]
    beatmap_playcounts_count: int
    country_code: str
    discord: Optional[str]
    follower_count: int
    interests: Optional[str]
    join_date: datetime
    pending_beatmapset_count: int
    graveyard_beatmapset_count: int
    loved_beatmapset_count: int
    ranked_and_approved_beatmapset_count: int
    ranked_beatmapset_count: int
    unranked_beatmapset_count: int
    mapping_follower_count: int
    scores_first_count: int
    title: Optional[str]
    twitter: Optional[str]
    user_achievements: list[dict]
    username: str
    statistics: Statistics
    website: Optional[str]
    rankHistory: Optional[dict]

    @property
    def rank_history(self) -> list[int]:
        return self.rankHistory['data']
