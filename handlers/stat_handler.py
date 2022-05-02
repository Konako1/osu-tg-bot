from aiogram import Router, F
from aiogram.types import Message
from collections import Counter

import config
from db import Db, CommandStat

router = Router()


def stat_builder(list_stat: list[CommandStat]) -> str:
    user_list = []
    command_stat: Counter[str, int] = Counter()
    for stat in list_stat:
        if stat.tg_user_id not in user_list:
            user_list.append(stat.tg_user_id)
        command_stat[stat.command] += 1
    result_message = 'Commands:\n'
    for command, count in sorted(command_stat.items()):
        result_message += f'{command.upper()}: {count}\n'
    result_message += f'\nUsers in total: {len(user_list)}'
    return result_message


@router.message(F.chat.id == config.REPORT_CHAT_ID, commands=['all_stat', 'as', 'a'])
async def stat_handler(message: Message, db: Db):
    list_stat = await db.get_all_stat()
    stat = stat_builder(list_stat)
    await message.answer(f'Stat for all time:\n\n{stat}')
