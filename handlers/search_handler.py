from typing import Union

from aiogram import Router, Bot
from aiogram.dispatcher.filters import CommandObject
from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery

from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import Db, BeatmapData, MusicData
from message_constructors.search_constructor import search_constructor

router = Router()


class NextPage(CallbackData, prefix='next_page'):
    cursor: int
    query: str


class Song(CallbackData, prefix='send_song'):
    music_id: int


@router.message(commands=['search'])
async def search(message: Message, db: Db, command: CommandObject, bot: Bot):
    args = command.args
    if args is None:
        return message.reply('Write map link with the command or try to find song by title, artist, mapper name.')

    music = await search_constructor(args, 0, db)

    if music:
        await message.reply(
            text=await create_message_text_beatmap(music)
            if isinstance(music[0], BeatmapData)
            else await create_message_text_music(music, db),
            reply_markup=await create_music_buttons(music, args, 0)
        )
        await db.save_command_stat(message.date, 'search', message.from_user.id)
        return
    else:
        return message.reply('Track not found :(')


async def create_music_buttons(music: list[Union[BeatmapData, MusicData]], args: str,
                               cursor: int) -> InlineKeyboardMarkup:
    x = InlineKeyboardBuilder()

    if cursor >= 1:
        x.button(
            text='⬅️⬅️⬅️',
            callback_data=NextPage(cursor=cursor - 1, query=args)
        )
    for i, song in enumerate(music):
        if i == 10:
            break
        x.button(
            text=f'{i + 1}. {song.artist} - {song.title}',
            callback_data=Song(music_id=song.music_id))
    if len(music) == 11:
        x.button(
            text='➡️➡️➡️',
            callback_data=NextPage(cursor=cursor + 1, query=args)
        )
    x.adjust(1, repeat=True)
    return x.as_markup()


async def create_message_text_beatmap(music: list[BeatmapData]) -> str:
    text = 'Songs found:'
    for i, song in enumerate(music):
        text += f'\n{i+1}. <b>{song.artist}</b> - <b>{song.title}</b> | by {song.mapper} | <b>{song.length // 60}:{song.length % 60}m</b>'
    return text


async def create_message_text_music(music: list[MusicData], db: Db) -> str:
    text = 'Songs found:'
    for i, song in enumerate(music):
        mappers, _ = await db.find_beatmaps_by_music_id(song.music_id)
        text += f'\n{i + 1}. <b>{song.artist}</b> - <b>{song.title}</b> | by {", ".join(f"<b>{mapper}</b>" for mapper in mappers)} | <b>{song.length // 60}:{song.length % 60}m</b>'
    return text


@router.callback_query(Song.filter())
async def send_song(query: CallbackQuery, db: Db, callback_data: Song):
    await query.answer()
    music_id = callback_data.music_id
    file_id = await db.get_file_id_by_music_id(music_id)
    mappers, beatmap_ids = await db.find_beatmaps_by_music_id(music_id)
    text = ''
    for mapper, beatmap_id in zip(mappers, beatmap_ids):
        text += f'https://osu.ppy.sh/beatmapsets/{beatmap_id} by {mapper}'
    await query.message.reply_audio(file_id, text)


@router.callback_query(NextPage.filter())
async def send_new_page(query: CallbackQuery, db: Db, callback_data: NextPage):
    await query.answer()
    cursor = callback_data.cursor
    args = callback_data.query
    music = await search_constructor(args, cursor, db)
    return query.message.edit_reply_markup(await create_music_buttons(music, args, cursor))
