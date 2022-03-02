from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(commands=['start'])
async def start_handler(message: Message):
    return message.answer("Hello, i'm an osu bot that can show:\n"
                          "- player's 5 best scores.\n"
                          "- player's recent score.\n"
                          "- player's profile.\n"
                          "I can also remember osu username to use commands above without writing it.")
