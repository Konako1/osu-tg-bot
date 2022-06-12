import humanize

from api_model.user_data import UserData
from message_constructors.score_info_constructors import get_score_as_text_mini
from message_constructors.utils.utils import build_flag, build_user_url, build_rank_history_line, build_combo_line, \
    parse_score_rank, build_social_media_line, build_user_rank_line, build_miss_line, parse_mods, build_position_line, \
    build_position_line_mini
from model.score import Score


def get_message_text_player(
        score: Score,
        user: UserData,
        score_rank_line: str,
        combo_line: str,
        miss_count: str,
        mods_line: str,
        star_rating: float,
        flag: str,
        user_url: str,
        user_rank_line: str,
        social_media: str,
        position: str,
) -> str:
    score = get_score_as_text_mini(
        score.beatmap_data.url,
        score.beatmapset.artist,
        score.beatmapset.title,
        score.beatmap_data.difficulty_name,
        score_rank_line,
        score.accuracy,
        combo_line,
        miss_count,
        mods_line,
        star_rating,
        score.pp,
        score.created_at,
        position,
    )
    return f"{flag} <b><a href='{user_url}'>{user.username}'s</a></b> profile:\n\n" \
           f"{user_rank_line}" \
           f'Highest pp play:\n' \
           f'{score}' \
           f'Play Count: <b>{user.statistics.play_count}</b>\n' \
           f'Play Time: <b>{round(user.statistics.play_time / (60 * 60), 2)}h</b>\n' \
           f'First Place Ranks: <b>{user.scores_first_count}</b>\n' \
           f'Hit Accuracy: <b>{round(user.statistics.hit_accuracy, 2)}%</b>\n' \
           f'Replays Watched by Others: <b>{user.statistics.replays_watched_by_others}</b>\n' \
           f'Lvl: <b>{user.statistics.level}</b>\n' \
           f'Achievements count: <b>{len(user.user_achievements)}</b>\n\n' \
           f'{social_media}' \
           f'Joined {humanize.naturalday(user.join_date, format="%d %B %Y")}'


def profile_message_constructor(user: UserData, best_score: Score, star_rating: float):
    flag = build_flag(user.country_code)
    user_url = build_user_url(user.id)
    rank_history_line = build_rank_history_line(user.rank_history)
    user_rank_line = build_user_rank_line(
        user.statistics.pp,
        user.statistics.global_rank,
        user.statistics.country_rank,
        flag,
        rank_history_line,
        user.rank_history[-1]
    )
    score_rank_line = parse_score_rank(best_score.rank)
    combo_line = build_combo_line(best_score.max_combo, best_score.beatmap_data.max_combo, best_score.perfect)
    miss_count = build_miss_line(best_score.statistics.count_miss)
    mods_line = parse_mods(best_score.mods)
    position_line = build_position_line_mini(best_score.position)
    social_media_line = build_social_media_line(user.discord, user.twitter, user.website)
    return get_message_text_player(
        best_score,
        user,
        score_rank_line,
        combo_line,
        miss_count,
        mods_line,
        star_rating,
        flag,
        user_url,
        user_rank_line,
        social_media_line,
        position_line,
    )
