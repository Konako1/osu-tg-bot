import asyncio

from aiogram import Bot
from aiogram.exceptions import RestartingTelegram, TelegramRetryAfter, TelegramNetworkError, TelegramServerError, TelegramAPIError
import config
from db import Db


message_v04 = 'Hello! This bot had been updated to version 0.4.\n\n' \
              'Update includes:\n' \
              '- Reworked top5 command (may be slow when called for the first time)\n' \
              '- Updated caching. Now bot should run faster due to saving beatmap infos and beatmap files.\n' \
              '- Internal code and project structure improvement, but who cares anyway :^)' \
              '\n\n' \
              "In the future I have plans to introduce /track command that tracks user's scores and sends them in the chat.\n" \
              "If you have any questions or suggestions please message me @Konako1."

message_v05 = 'Hello there. This bot had been updated to version 0.5.\n\n' \
              'Update includes:\n' \
              '- New /search command which can be used to find songs by beatmap link or title, artis, mapper name.\n' \
              '\n\n' \
              "If you have any questions or suggestions please message me @Konako1."


async def get_tg_ids(db: Db) -> list[int]:
    result = await db.get_all_tg_id()
    return result


def get_message_text() -> str:
    return message_v05


async def send_message(bot: Bot, tg_id: int, text: str):
    try:
        await bot.send_message(tg_id, text)
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await send_message(bot, tg_id, text)
    except (RestartingTelegram, TelegramNetworkError, TelegramServerError) as e:
        await asyncio.sleep(1)
        return await send_message(bot, tg_id, text)
    except TelegramAPIError as e:
        print(e)
        return False
    return True


async def main():
    db = await Db.connect(config.DB_USER, config.DB_PASSWORD, config.DB_HOST, config.DB_NAME)
    bot = Bot(config.TG_TOKEN)
    text = get_message_text()
    ids = await get_tg_ids(db)
    for tg_id in ids:
        result = await send_message(bot, tg_id, text)
        if not result:
            await db.remove_user_from_remember_me(tg_id)
        await asyncio.sleep(0.05)
    await bot.session.close()
    await db.close()
    await asyncio.sleep(0.1)


if __name__ == '__main__':
    asyncio.run(main())
