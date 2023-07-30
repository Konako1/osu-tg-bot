import asyncio
import operator
from functools import reduce
from typing import Iterator

import pyttanko
from pyttanko import beatmap

from api_model.base_score import Statistics
from api_model.beatmap import BeatmapData
from model.performance import Performance, PerformanceList, PerformanceListStat
from model.score import Score
from requests.osu_tools_request import OsuToolsRequest

pyttanko_parser = pyttanko.parser()


def get_expanded_beatmap_file(osu_file: Iterator[str]) -> beatmap:
    return pyttanko_parser.map(osu_file)


def recalculate_mods(mods: list[str]):
    mods_calc = reduce(operator.or_,
                       (getattr(pyttanko, f'MODS_{mod}') for mod in mods if mod != 'PF' and mod != 'SD'),
                       pyttanko.MODS_NOMOD)
    return mods_calc


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


def get_pp_flexible(
        accuracy: float,
        mods: list[str],
        beatmap_data: BeatmapData,
        star_rating,
        expanded_beatmap_file: beatmap
) -> float:
    mods_calc = recalculate_mods(mods)
    objects = beatmap_data.count_circles + beatmap_data.count_sliders + beatmap_data.count_spinners
    fail_acc = pyttanko.acc_round(round(accuracy * 100), objects, 0)
    pp, *_ = pyttanko.ppv2(star_rating.aim, star_rating.speed, mods=mods_calc, bmap=expanded_beatmap_file,
                           n300=fail_acc[0],
                           n100=fail_acc[1],
                           n50=fail_acc[2],
                           nmiss=0)
    return pp


async def performance_list_request(score: Score, osu_tools_request: OsuToolsRequest) -> PerformanceList:
    base = pp_request(score.beatmap.id, score, osu_tools_request)
    fc = pp_request_if_fc(score.beatmap.id, score, osu_tools_request)
    ss = pp_request_if_ss(score.beatmap.id, score, osu_tools_request)

    request = await asyncio.gather(base, fc, ss)
    return PerformanceList(
        base=request[0],
        fc=request[1],
        ss=request[2]
    )


def parse_osu_tools_data(data: dict, score: Score) -> Performance:
    mods = data['mods'].split(', ').remove('CL')

    hp = score.beatmap_data.hp
    cs = score.beatmap_data.cs
    for mod in mods:
        if mod.lower() == 'ez':
            hp *= 0.5
            cs *= 0.5
        if mod.lower() == 'hr':
            cs *= 1.3
            hp *= 1.4

    return Performance(
        pp=data['pp'],
        star_rating=data['star rating'],
        acc=data['acc'],
        combo=data['combo'],
        max_combo=data['max combo'],
        mods=mods,
        great=data['great'],
        ok=data['ok'],
        meh=data['meh'],
        miss=data['miss'],
        ar=data['approach rate'],
        od=data['overall difficulty'],
        cs=cs,
        hp=hp,
        aim_pp=data['aim'],
        speed_pp=data['speed'],
        accuracy_pp=data['accuracy'],
        flashlight_pp=data['flashlight'],
        effective_miss_count=data['effective miss count'],
        aim_difficulty=data['aim difficulty'],
        speed_difficulty=data['speed difficulty'],
        speed_note_count=data['speed note count'],
        flashlight_difficulty=data['flashlight difficulty'],
        slider_factor=data['slider factor'],
        beatmap=data['beatmap'],
    )


async def pp_request(beatmap_id: int, score: Score, osu_tools_request: OsuToolsRequest) -> Performance:
    data = await osu_tools_request.play_performance(
        beatmap_id,
        score.max_combo,
        score.mods,
        score.statistics.count_miss,
        score.statistics.count_100,
        score.statistics.count_50
    )

    return parse_osu_tools_data(data, score)


async def pp_request_if_fc(beatmap_id: int, score: Score, osu_tools_request: OsuToolsRequest) -> Performance:
    data = await osu_tools_request.play_performance_if_fc(
        beatmap_id,
        score.mods,
        score.statistics.count_100,
        score.statistics.count_50
    )

    return parse_osu_tools_data(data, score)


async def pp_request_if_ss(beatmap_id: int, score: Score, osu_tools_request: OsuToolsRequest) -> Performance:
    data = await osu_tools_request.play_performance_if_ss(
        beatmap_id,
        score.mods,
    )

    return parse_osu_tools_data(data, score)


async def pp_request_flexible(beatmap_id: int, score: Score, osu_tools_request: OsuToolsRequest) -> PerformanceListStat:
    objects_count = score.beatmap_data.count_circles + score.beatmap_data.count_sliders + score.beatmap_data.count_spinners
    goods_count = [
        0,                                  # 100%
        int(objects_count / 66.6),          # 99%
        int(objects_count / (66.6 / 2)),    # 98%
        int(objects_count / (66.6 / 3)),    # 97%
        int(objects_count / (66.6 / 5)),    # 95%
    ]
    requests = []
    for good in goods_count:
        requests.append(
            osu_tools_request.play_performance_if_fc(
                beatmap_id,
                score.mods,
                good,
                0
            ))

    response = await asyncio.gather(*requests)
    return PerformanceListStat(
        acc100=parse_osu_tools_data(response[0], score),
        acc99=parse_osu_tools_data(response[1], score),
        acc98=parse_osu_tools_data(response[2], score),
        acc97=parse_osu_tools_data(response[3], score),
        acc95=parse_osu_tools_data(response[4], score),
    )


