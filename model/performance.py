from dataclasses import dataclass


@dataclass
class Performance:
    pp: float
    star_rating: float
    acc: float
    combo: int
    max_combo: int
    mods: list[str]
    great: int
    ok: int
    meh: int
    miss: int
    ar: float
    od: float
    hp: float
    cs: float
    aim_pp: float
    speed_pp: float
    accuracy_pp: float
    flashlight_pp: float
    effective_miss_count: float
    aim_difficulty: float
    speed_difficulty: float
    speed_note_count: float
    flashlight_difficulty: float
    slider_factor: float
    beatmap: str


@dataclass
class PerformanceList:
    base: Performance
    fc: Performance
    ss: Performance


@dataclass
class PerformanceListStat:
    acc100: Performance
    acc99: Performance
    acc98: Performance
    acc97: Performance
    acc95: Performance
