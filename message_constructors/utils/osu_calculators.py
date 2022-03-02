import operator
from functools import reduce
from typing import Iterator

import pyttanko
from pyttanko import beatmap

from api_model.base_score import Statistics
from api_model.beatmap import BeatmapData
from model.score import Score

pyttanko_parser = pyttanko.parser()


def get_expanded_beatmap_file(osu_file: Iterator[str]) -> beatmap:
    return pyttanko_parser.map(osu_file)


def recalculate_mods(mods: list[str]):
    mods_calc = reduce(operator.or_,
                       (getattr(pyttanko, f'MODS_{mod}') for mod in mods if mod != 'PF' and mod != 'SD'),
                       pyttanko.MODS_NOMOD)
    return mods_calc


def get_converted_star_rating(mods: list[str], expanded_beatmap_file: beatmap):
    mods_calc = recalculate_mods(mods)
    return pyttanko.diff_calc().calc(expanded_beatmap_file, mods_calc)


def get_pp_for_score(
        accuracy: float,
        score_max_combo: int,
        pp: float,
        mods: list[str],
        beatmap_data: BeatmapData,
        statistics: Statistics,
        star_rating,
        expanded_beatmap_file: beatmap
) -> tuple[float, float, float]:
    mods_calc = recalculate_mods(mods)
    objects = beatmap_data.count_circles + beatmap_data.count_sliders + beatmap_data.count_spinners
    fail_acc = pyttanko.acc_round(round(accuracy * 100), objects, statistics.count_miss)
    ss_pp, *_ = pyttanko.ppv2(star_rating.aim, star_rating.speed, mods=mods_calc, bmap=expanded_beatmap_file)
    fc_pp, *_ = pyttanko.ppv2(star_rating.aim, star_rating.speed, mods=mods_calc, bmap=expanded_beatmap_file,
                              n300=fail_acc[0] + statistics.count_miss,
                              n100=fail_acc[1],
                              n50=fail_acc[2],
                              nmiss=0)
    if pp is None:
        score_pp, *_ = pyttanko.ppv2(star_rating.aim, star_rating.speed, mods=mods_calc, bmap=expanded_beatmap_file,
                                     n100=statistics.count_100,
                                     n50=statistics.count_50,
                                     nmiss=statistics.count_miss,
                                     combo=score_max_combo)
    else:
        score_pp = pp
    return score_pp, fc_pp, ss_pp
