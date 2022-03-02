from aiogram import Router
from aiogram.dispatcher.filters import CommandObject
from aiogram.types import Message

from db import Db
from message_constructors.utils.cache_check import bind_osu_id_with_tg_id
from request import Request

router = Router()


@router.message(commands=['remember_me'])
async def remember_me_handler(message: Message, request: Request, db: Db, command: CommandObject):
    username = command.args
    if username is None:
        return message.reply('You forgot to write a nickname to remember.')
    result = await bind_osu_id_with_tg_id(username, db, request, message.from_user.id)
    if result == 0:
        return message.reply('User not found.')
    await message.reply('Remembered!')
    await db.save_command_stat(message.date, 'remember_me', message.from_user.id)
