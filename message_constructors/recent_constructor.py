from datetime import datetime
from html import escape
from typing import Iterator

from api_model.user_data import UserData
from message_constructors.score_info_constructors import get_score_as_text_full
from message_constructors.utils.osu_calculators import get_expanded_beatmap_file, get_converted_star_rating
from message_constructors.utils.utils import build_flag, build_user_url, parse_mods, build_combo_line, build_miss_line, \
    parse_score_rank, build_completed_percentage_line, get_pp_line, is_star_rating_right, build_position_line
from model.score import Score
import humanize


def get_message_text(
        score: Score,
        star_rating: float,
        mods: str,
        combo_line: str,
        miss_line: str,
        rank: str,
        completed_line: str,
        pp_line,
        flag: str,
        global_rank: int,
        user_url: str,
        username: str,
        score_time: str,
        position: str,
) -> str:
    score = get_score_as_text_full(
        score.beatmap_data.url,
        score.beatmapset.artist,
        score.beatmapset.title,
        score.beatmap_data.difficulty_name,
        score.beatmapset.creator,
        star_rating,
        mods,
        combo_line,
        miss_line,
        score.accuracy,
        rank,
        score.beatmap_data.status,
        completed_line,
        pp_line,
        position,
    )
    return f"(#{global_rank}) {flag} <a href='{user_url}'>{username}'s</a>"\
           f" latest score ({score_time}):\n\n"\
           f"{score}"


def recent_message_constructor(score: Score, user: UserData, message_date: datetime, osu_file: Iterator[str]) -> str:
    flag = build_flag(user.country_code)
    user_url = build_user_url(score.user_id)
    score_time = humanize.naturaltime(message_date - score.created_at)
    mods = parse_mods(score.mods)
    combo_line = build_combo_line(score.max_combo, score.beatmap_data.max_combo, score.perfect)
    miss_line = build_miss_line(score.statistics.count_miss)
    position_line = build_position_line(score.position)
    parsed_rank = parse_score_rank(score.rank)
    expanded_beatmap_file = get_expanded_beatmap_file(osu_file)
    stars = get_converted_star_rating(score.mods, expanded_beatmap_file)
    star_rating = score.beatmap_data.stars \
        if is_star_rating_right(mods) \
        else stars.total
    completed_line = build_completed_percentage_line(score.statistics, score.beatmap_data)
    pp_line = get_pp_line(score, parsed_rank, stars, expanded_beatmap_file)
    message = get_message_text(
        score,
        star_rating,
        mods,
        combo_line,
        miss_line,
        parsed_rank,
        completed_line,
        pp_line,
        flag,
        user.rankHistory['data'][-1],
        user_url,
        user.username,
        score_time,
        position_line,
    )
    return message
