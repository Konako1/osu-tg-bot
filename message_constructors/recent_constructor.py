from datetime import datetime
from html import escape
from typing import Iterator

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api_model.beatmap import BeatmapData
from api_model.user_data import UserData
from handlers.recent_handler import Stat
from message_constructors.score_info_constructors import get_score_as_text_full
from message_constructors.utils.osu_calculators import get_expanded_beatmap_file, get_converted_star_rating, \
    get_pp_flexible
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


def get_stat_message_text(
        beatmap_data: BeatmapData,
        artist: str,
        title: str,
        creator: str,
        difficulty_name: str,
        link: str,
        bpm: float,
        stars: float,
        length: int,
        pp_line: str,
) -> str:
    return f"Statistic for <a href='{link}'>{escape(artist)} - {escape(title)} " \
           f"[{escape(difficulty_name)}] by {escape(creator)}</a>\n\n" \
           f"<b>Beatmap data:</b>\n" \
           f"{round(bpm)} bpm | {round(stars, 2)}★ | Length: {length // 60}:{length%60}\n" \
           f"Circles: {beatmap_data.count_circles} | Sliders: {beatmap_data.count_sliders} | Spinners: {beatmap_data.count_spinners}\n" \
           f"AR: {beatmap_data.ar}\nOD: {beatmap_data.od}\nCS: {beatmap_data.cs}\nHP: {beatmap_data.hp}\n\n" \
           f"<b>PP data:</b>\n" \
           f"{pp_line}"


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


def recent_message_stat_constructor(score: Score, osu_file: Iterator[str]) -> str:
    expanded_beatmap_file = get_expanded_beatmap_file(osu_file)
    stars = get_converted_star_rating(score.mods, expanded_beatmap_file)
    acc = [1.0, 0.99, 0.98, 0.97, 0.95]
    pp_line = ''
    for a in acc:
        pp = get_pp_flexible(
            a,
            score.mods,
            score.beatmap_data,
            stars,
            expanded_beatmap_file
        )
        pp_line += f'<b>{round(pp, 2)}pp</b> for <b>{round(a * 100)}%</b>\n'
    message = get_stat_message_text(
        score.beatmap_data,
        score.beatmapset.artist,
        score.beatmapset.title,
        score.beatmapset.creator,
        score.beatmap_data.difficulty_name,
        score.beatmap_data.url,
        score.beatmap_data.bpm,
        stars.total,
        score.beatmap_data.total_length,
        pp_line
    )
    return message


def create_stat_button(score_id: int, text: str, is_stat: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=text,
        callback_data=Stat(score_id=score_id, is_stat=is_stat)
    )
    return kb.as_markup()
