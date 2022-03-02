import asyncio
import datetime

import humanize
from aiogram import Bot

import config
from db import Db
from handlers.stat_handler import stat_builder


async def everyday_stat_handler():
    db = await Db.connect(config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME)
    list_stat = await db.get_all_stat(datetime.datetime.utcnow())
    await db.close()
    if not list_stat:
        return
    stat = stat_builder(list_stat)
    bot = Bot(config.TG_TOKEN)
    await bot.send_message(
        config.REPORT_CHAT_ID,
        f'Stat for {humanize.naturalday(list_stat[0].date)}:\n\n{stat}'
    )
    await bot.session.close()
    await asyncio.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(everyday_stat_handler())
