from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery

from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import Db, MusicData
from message_constructors.search_constructor import search_constructor

router = Router()


class NextPage(CallbackData, prefix='next_page'):
    cursor: int
    query: str


class Song(CallbackData, prefix='send_song'):
    beatmap_id: int


@router.message(commands=['search'])
async def search(message: Message, db: Db, command: CommandObject, bot: Bot):
    args = command.args
    if args is None:
        return message.reply('Write map link with the command or try to find song by title, artist, mapper name.')

    music = await search_constructor(args, 0, db)

    if music:
        await message.reply('Songs found:', reply_markup=await create_music_buttons(music, args, 0))
        await db.save_command_stat(message.date, 'search', message.from_user.id)
        return
    else:
        return message.reply('Track not found :(')


async def create_music_buttons(music: list[MusicData], args: str, cursor: int) -> InlineKeyboardMarkup:
    x = InlineKeyboardBuilder()

    if cursor >= 1:
        x.button(
            text='⬅️⬅️⬅️',
            callback_data=NextPage(cursor=cursor-1, query=args)
        )
    for i, song in enumerate(music):
        if i == 10:
            break
        x.button(
            text=f'{song.artist} - {song.title} | by {song.mapper} | {song.length//60}:{song.length%60}m',
            callback_data=Song(beatmap_id=song.beatmap_id))
    if len(music) == 11:
        x.button(
            text='➡️➡️➡️',
            callback_data=NextPage(cursor=cursor+1, query=args)
        )
    x.adjust(1, repeat=True)
    return x.as_markup()


@router.callback_query(Song.filter())
async def send_song(query: CallbackQuery, db: Db, callback_data: Song):
    await query.answer()
    beatmap_id = callback_data.beatmap_id
    music = await db.find_music_by_id(beatmap_id)
    for song in music:
        await query.message.reply_audio(song.file_id, f'https://osu.ppy.sh/beatmapsets/{beatmap_id}')


@router.callback_query(NextPage.filter())
async def send_new_page(query: CallbackQuery, db: Db, callback_data: NextPage):
    await query.answer()
    cursor = callback_data.cursor
    args = callback_data.query
    music = await search_constructor(args, cursor, db)
    return query.message.edit_reply_markup(await create_music_buttons(music, args, cursor))
