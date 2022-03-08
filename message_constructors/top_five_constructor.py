import os
from dataclasses import dataclass
from io import BytesIO
from pprint import pprint
from typing import Iterator

from PIL import ImageOps, ImageDraw, ImageFont
from PIL import Image

from api_model.user_data import UserData
from message_constructors.score_info_constructors import get_score_as_text_mini
from message_constructors.utils.cache_check import get_saved_pic, save_pic
from message_constructors.utils.osu_calculators import get_expanded_beatmap_file, get_converted_star_rating
from message_constructors.utils.utils import build_combo_line, parse_mods, build_user_url, build_flag, \
    is_star_rating_right, parse_score_rank, build_miss_line, build_position_line_mini
from model.score import Score


@dataclass
class MapData:
    image: Image.Image
    pp_value: int
    position: int
    x: int


# TODO: write pp and score place on bg || 09.02.2022
def thumbnail_maker(image_list: list[Image.Image], pp_list: list[int] = [1, 1, 1, 1, 1]) -> BytesIO:
    parts = []
    plays_data = [
        MapData(image_list[3], pp_list[3], 4, 80),
        MapData(image_list[1], pp_list[1], 2, 120),
        MapData(image_list[0], pp_list[0], 1, 90),
        MapData(image_list[2], pp_list[2], 3, 100),
        MapData(image_list[4], pp_list[4], 5, 130),
    ]
    for i, play in enumerate(plays_data):
        for mask_file in os.listdir('images/mask/'):
            if mask_file.startswith(str(i+1)):
                mask = Image.open(f'images/mask/{mask_file}').convert('L')
                part = ImageOps.fit(play.image, mask.size, centering=(0.5, 0.5))
                part.putalpha(mask)
                # draw = ImageDraw.Draw(part)
                # font = ImageFont.truetype("images/fonts/microsoftsansserif.ttf", 40)
                # draw.text((play.x, 100),
                #           f"#{play.position}\n{play.pp_value}pp",
                #           (255, 255, 255),
                #           font=font,
                #           align='center',
                #           stroke_fill='black',
                #           stroke_width=3)
                parts.append(part)

    bg = Image.new('RGB', (1160, 300), 'white')
    indent = [0, 109, 155, 226, 340]
    for i, part in enumerate(parts):
        bg.paste(part, (300 * i - indent[i], 0, 300 + 300 * i - indent[i], 300), part)
    tmp = BytesIO()
    bg.save(tmp, 'png')
    return tmp


def top_five_message_constructor(scores: list[Score], user: UserData, osu_files: list[Iterator[str]]) -> str:
    user_url = build_user_url(user.id)
    flag = build_flag(user.country_code)
    message = f"{flag} <b><a href='{user_url}'>{user.username}'s</a> (#{user.rankHistory['data'][-1]})</b> best scores:\n\n"
    for i, score in enumerate(scores):
        rank_line = parse_score_rank(score.rank)
        combo_line = build_combo_line(score.max_combo, score.beatmap_data.max_combo, score.perfect)
        mods_line = parse_mods(score.mods)
        expanded_beatmap_file = get_expanded_beatmap_file(osu_files[i])
        miss_count = build_miss_line(score.statistics.count_miss)
        position_line = build_position_line_mini(score.position)
        star_rating = score.beatmap_data.stars \
            if is_star_rating_right(mods_line) \
            else get_converted_star_rating(score.mods, expanded_beatmap_file).total
        score = get_score_as_text_mini(
            score.beatmap_data.url,
            score.beatmapset.artist,
            score.beatmapset.title,
            score.beatmap_data.difficulty_name,
            rank_line,
            score.accuracy,
            combo_line,
            miss_count,
            mods_line,
            star_rating,
            score.pp,
            score.created_at,
            position_line,
        )
        message += f'<b>#{i + 1}</b> {score}'
    return message
