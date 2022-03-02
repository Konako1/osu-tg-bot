from aiogram import Router, F
from aiogram.types import Message

import config
from db import Db, CommandStat

router = Router()


def stat_builder(list_stat: list[CommandStat]) -> str:
    user_list = []
    command_stat = {
        'recent': 0,
        'profile': 0,
        'top5': 0,
        'remember_me': 0,
    }
    for stat in list_stat:
        if stat.tg_user_id not in user_list:
            user_list.append(stat.tg_user_id)
        command_stat[stat.command] += 1
    return ('Commands:\n'
            f'Recent: {command_stat["recent"]}\n'
            f'Profile: {command_stat["profile"]}\n'
            f'Top 5: {command_stat["top5"]}\n'
            f'Remembered users: {command_stat["remember_me"]}\n'
            f'\nUsers in total: {len(user_list)}')


@router.message(F.chat.id == config.REPORT_CHAT_ID, commands=['all_stat', 'as', 'a'])
async def stat_handler(message: Message, db: Db):
    list_stat = await db.get_all_stat()
    stat = stat_builder(list_stat)
    await message.answer(f'Stat for all time:\n\n{stat}')
