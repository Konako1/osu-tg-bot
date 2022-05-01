import asyncio
import re
from collections import Counter

from PIL import Image
from pyttanko import beatmap

from api_model.base_score import Statistics
from api_model.beatmap import BeatmapData
from db import Db
from message_constructors.utils.cache_check import save_pic, get_saved_pic, get_osu_file
from message_constructors.utils.class_constructor import create_score_class
from message_constructors.utils.osu_calculators import get_pp_for_score
from model.score import Score
from request import Request


def build_flag(code: str) -> str:
    flag = "".join(chr(ord("🇦") + (ord(x.lower()) - ord("a"))) for x in f"{code}")
    return flag


def build_user_url(user_id: int) -> str:
    return f"https://osu.ppy.sh/users/{user_id}"


def parse_mods(mods_dict: list[str]) -> str:
    mods = ''.join(mods_dict)
    if mods == '':
        mods = 'NM'
    return mods


def is_star_rating_right(mods_line: str) -> bool:
    not_default_sr_mods = ['HR', 'DT', 'NC', 'EZ', 'HT', 'FL']
    for mod in not_default_sr_mods:
        if mod in mods_line:
            return False
    return True


def build_combo_line(combo: int, max_combo: int, is_perfect: bool) -> str:
    if is_perfect:
        return 'FC'
    return f'{combo}x/{max_combo}x'


def build_miss_line(miss_count: int) -> str:
    if miss_count == 0:
        return ''
    return f' | {miss_count}x Miss'


def build_position_line(position: int) -> str:
    if position is None:
        return ''
    position = f'<b>#{position}</b>' if position <= 50 else f'#{position}'
    return f'| Achieved {position}'


def build_position_line_mini(position: int) -> str:
    if position is None:
        return ''
    return f'| #{position} on a map'


def parse_score_rank(rank: str) -> str:
    ranks = {
        'XH': "SS+",
        'X': "SS",
        'SH': 'S+'
    }
    return ranks.get(rank, rank)


def build_completed_percentage_line(statistics: Statistics, beatmap_data: BeatmapData) -> str:
    percent = round((statistics.count_miss
                    + statistics.count_50
                    + statistics.count_100
                    + statistics.count_300) /
                    (beatmap_data.count_circles
                    + beatmap_data.count_sliders
                    + beatmap_data.count_spinners) * 100, 2)
    if percent == 100.0:
        return ''
    return f'Completed: {percent}% of the map\n'


def build_rank_history_line(ranks: list[int]) -> str:
    rank_change = ranks[-7] - ranks[-1]
    sign = 'gained' if rank_change >= 0 else 'lost'
    return f'{abs(rank_change)} ranks {sign} for the past week'


def build_social_media_line(d: str, t: str, w: str) -> str:
    if d is None and t is None and w is None:
        return ''
    discord = f'Discord: <b>{d}</b>\n' if d is not None else ''
    twitter = f'Twitter: <b><a href="https://twitter.com/{t}">@{t}</a></b>\n' if t is not None else ''
    website = f'Website: <b>{w}</b>\n' if w is not None else ''
    return f'Social media:\n' \
           f'{discord + twitter + website}\n'


def build_user_rank_line(
        pp: float,
        global_rank: int,
        country_rank: int,
        flag: str,
        rank_history_line: str,
        last_rank: int
) -> str:
    if global_rank is None or country_rank is None:
        return f'<b>User is inactive | #{last_rank}</b> [{rank_history_line}]\n\n'
    return f'<b>{round(pp)}pp | #{global_rank}</b> ' \
           f'({flag} #{country_rank}) [{rank_history_line}]\n\n'


def get_pp_line(score: Score, rank: str, stars, expanded_beatmap_file: beatmap) -> str:
    pp, fc_pp, ss_pp = get_pp_for_score(
        score.accuracy,
        score.max_combo,
        score.pp,
        score.mods,
        score.beatmap_data,
        score.statistics,
        stars,
        expanded_beatmap_file,
    )
    pp_line = f'{round(pp, 2)}pp'
    fc_pp_line = f'{round(fc_pp, 2)}pp'
    ss_pp_line = f'{round(ss_pp, 2)}pp'
    if rank == 'SS' or rank == 'SS+':
        return pp_line
    if score.perfect:
        return f'{pp_line} | {ss_pp_line} if SS'
    if rank == 'F':
        return f'{fc_pp_line} if FC | {ss_pp_line} if SS'
    return f'{pp_line} | {fc_pp_line} if FC | {ss_pp_line} if SS'


async def get_saved_image(beatmap_id: int, img_link: str, request: Request) -> Image.Image:
    img = get_saved_pic('map_bg_cover', beatmap_id)
    if img is None:
        byte_cover = await request.get_pic_as_bytes(img_link)
        img = save_pic('map_bg_cover', beatmap_id, byte_cover)
    return img


async def get_id_list(args: str, db: Db) -> list[int]:
    id_count: Counter[int, int] = Counter()
    divided_args = re.findall('([a-z0-9]*)', args, re.IGNORECASE)
    for word in divided_args:
        id_list = await db.get_id_by_token(word)
        id_count.update(id_list)
    return [x[0] for x in id_count.most_common()]


# TODO: try to compress requests in one function
async def gather_requests(awaitable_list: list, operation: str, request: Request, db: Db) -> list:
    result_list = []
    if operation == 'score':
        for item in awaitable_list:  # type: dict
            result_list.append(create_score_class(item, request, db))
    elif operation == 'osu_file':
        for item in awaitable_list:  # type: Score
            result_list.append(get_osu_file(item.beatmap.id, item.beatmap.last_updated, request))
    elif operation == 'image':
        for item in awaitable_list:  # type: Score
            result_list.append(get_saved_image(item.beatmap.id, item.beatmapset.square_cover, request))
    result = await asyncio.gather(*result_list)
    return [item for item in result]
