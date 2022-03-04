import asyncio

from aiogram import Bot

import config
from db import Db


async def get_tg_ids() -> list[int]:
    db = await Db.connect(config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME)
    result = await db.get_all_tg_id()
    db.close()
    return result


def get_message_text() -> str:
    return 'Hello! This bot had been updated to version 0.4.\n\n' \
           'Update includes:\n' \
           '- Reworked top5 command (may be slow when called for the first time)\n' \
           '- Updated caching. Now bot should run faster due to saving beatmap infos and beatmap files.\n' \
           '- Internal code and project structure improvement, but who cares anyway :^)' \
           '\n\n' \
           "In the future I have plans to introduce /track command that tracks user's scores and sends them in the chat.\n" \
           "If you have any questions or suggestions please message me @Konako1."


async def main():
    bot = Bot(config.TG_TOKEN)
    text = get_message_text()
    ids = await get_tg_ids()
    for tg_id in ids:
        await bot.send_message(tg_id, text)
        await asyncio.sleep(0.05)
    await bot.session.close()
    await asyncio.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())
