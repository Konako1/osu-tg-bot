from datetime import datetime
from html import escape

import humanize


def get_score_as_text_full(
        beatmap_url: str,
        artist: str,
        title: str,
        difficulty_name: str,
        creator: str,
        star_rating: float,
        mods: str,
        combo_line: str,
        miss_line: str,
        accuracy: float,
        rank: str,
        beatmap_status: str,
        completed_line: str,
        pp_line: str,
        position: str,
) -> str:
    return f"<a href='{beatmap_url}'>{escape(artist)} — {escape(title)}"\
           f' [{escape(difficulty_name)}]</a> '\
           f'by {creator} | {round(star_rating, 2)}★ <b>+{mods}</b>\n\n'\
           f"{combo_line}{miss_line} {position}\n"\
           f"<b>{round(accuracy * 100, 2)}% | {rank}</b>\n"\
           f"{beatmap_status.capitalize()}\n"\
           f"{completed_line}\n<b>{pp_line}</b>"


def get_score_as_text_mini(
        beatmap_url: str,
        artist: str,
        title: str,
        difficulty_name: str,
        rank_line: str,
        accuracy: float,
        combo_line: str,
        miss_count: str,
        mods_line: str,
        star_rating: float,
        pp: float,
        date_creation: datetime,
        position: str,
) -> str:
    return f"<b><a href='{beatmap_url}'>{artist} - {title} [{difficulty_name}]</a></b>\n" \
           f"<b>{rank_line} {round(accuracy * 100, 2)}% | {combo_line}{miss_count} | ({mods_line}) {round(star_rating, 2)}★</b>\n" \
           f"<b>{round(pp, 2)}pp {position}</b>\n" \
           f"{humanize.naturalday(date_creation, format='%d %B %Y')}\n\n"
