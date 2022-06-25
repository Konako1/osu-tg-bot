import html
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, Update

from db import Db
from config import DB_NAME, DB_HOST, DB_USER, DB_PASSWORD, REPORT_CHAT_ID
from config import TG_TOKEN
from handlers import recent_handler, top_five_handler, profile_handler, remember_me_handler, start_handler, \
    stat_handler, search_handler
from config import TG_TOKEN, DB_NAME, DB_HOST, DB_USER, DB_PASSWORD
from request import create_request
from traceback import format_exc
import logging

dp = Dispatcher()


@dp.errors()
async def errors_handler(update: Update, exception: Exception, bot: Bot):
    message = f'While handling <code>{update.message.text}</code> an error occurred:\n' \
              f'<b>{exception.__class__.__name__}</b>: <code>{html.escape(format_exc(exception))}</code>' \
              f'\n\nIn chat: <code>{update.message.chat.id}</code>'
    await bot.send_message(REPORT_CHAT_ID, message)


@dp.startup()
async def on_startup(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command='recent', description="Get user's recent score"),
        BotCommand(command='profile', description="Get user's profile"),
        BotCommand(command='top5', description="Get user's 5 best plays"),
        BotCommand(command='search', description="Search music from osu!"),
        BotCommand(command='remember_me', description="Remember user's nickname for commands"),
    ])


async def main():
    bot = Bot(TG_TOKEN, parse_mode='HTML')
    db = await Db.connect(DB_USER, DB_PASSWORD, DB_HOST, DB_NAME)
    dp.include_router(recent_handler.router)
    dp.include_router(top_five_handler.router)
    dp.include_router(profile_handler.router)
    dp.include_router(remember_me_handler.router)
    dp.include_router(search_handler.router)
    dp.include_router(start_handler.router)
    dp.include_router(stat_handler.router)
    await dp.start_polling(bot, request=await create_request(), db=db)


if __name__ == '__main__':
    asyncio.run(main())
