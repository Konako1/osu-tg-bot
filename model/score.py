from dataclasses import dataclass
from typing import Iterator, Optional

from api_model.beatmap import Beatmap, BeatmapData
from api_model.beatmapset import Beatmapset
from api_model.base_score import BaseScore
from api_model.user_data import UserData


class Score(BaseScore):
    beatmap_data: BeatmapData
    position: Optional[int]
