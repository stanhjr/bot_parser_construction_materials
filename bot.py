# -*- coding: utf-8 -*-
# !/usr/bin/env python
import asyncio
import json
import logging
import os
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot as AiogramBot, executor, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter, Text
from aiogram.types import ChatType

from celery_parser.tasks import add_table, regular_parsing

from config import BOT_TOKEN, BOT_NICKNAME

from handler import (
    get_by_groups,
    get_by_products,
)
from markup import get_admin_keyboard, get_count_of_parsing_keyboard, get_cancel_menu, get_user_keyboard, \
    get_employees_for_bind
from redis_api import redis_api
from models.data_api import data_api
from state import SetParserCount, AddTable, DeleteEmployee
from utils import (
    Pagination,
    get_table,
    get_groups,
    get_products,
    set_lsid,
    get_lsid,
    get_admins,
)

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(level="WARNING")
logging.basicConfig(filename=f"logs/{datetime.now().strftime('%Y-%m-%d %H-%M')}.log", level="WARNING")

loop = asyncio.get_event_loop()
bot = AiogramBot(token=BOT_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage, loop=loop)

scheduler = AsyncIOScheduler()

symbols = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
           'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
           'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def is_time(time_string: str) -> bool:
    try:
        datetime.strptime(time_string, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


async def extract_unique_code(text):
    # Extracts the unique_code from the sent /start command.
    return text.split()[1] if len(text.split()) > 1 else None


@dp.message_handler(text="❌Отмена", state='*')
async def cancel_currency(message: types.Message, state: FSMContext):
    if message.from_user.id in get_admins():
        reply_markup = get_admin_keyboard()
        await state.reset_data()
        await state.finish()
        await message.answer(text="Операция отменена", reply_markup=reply_markup)


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    if message.from_user.id in get_admins():
        data_api.create_employee(message)
        text = 'Добро пожаловать в меню администратора!\nПожалуйста, выберите одно из доступных действий:'
        await message.answer(text=text, reply_markup=get_admin_keyboard())
    else:
        unique_code = await extract_unique_code(message.text)
        if unique_code:
            if unique_code in storage.data['codes'].keys():
                data_api.create_employee(message)
                text = 'Добро пожаловать в гланое меню бота!\nПожалуйста, выберите одно из доступных действий:'
                await message.answer(text=text, reply_markup=get_user_keyboard())


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), text='🕘 Время Парсинга')
async def set_time_to_parsing_start(message: types.Message, state: FSMContext):
    user_id = message.chat.id
    if user_id in get_admins():
        text = 'Cколько раз в сутки вы хотите парсить цены'
        msg = await message.answer(text=text, reply_markup=get_count_of_parsing_keyboard())
        await state.update_data(user_message_id=message.message_id)
        await state.update_data(bot_message_id=msg.message_id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('pars_'))
async def create_set_time_to_parsing_1(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        if callback_query.from_user.id in get_admins():
            data = await state.get_data()

            if callback_query.data[5:] == "cancel":
                reply_markup = get_admin_keyboard()

                await bot.delete_message(callback_query.from_user.id, data.get("bot_message_id"))
                await bot.delete_message(callback_query.from_user.id, data.get("user_message_id"))
                await bot.send_message(callback_query.from_user.id, text="Операция отменена", reply_markup=reply_markup)
                await state.finish()
            else:
                steps_count = int(callback_query.data[5:])
                step = 1
                await state.update_data(steps_count=steps_count)
                await state.update_data(step=1)
                text = f"Введите время шаг {step} из {steps_count}"
                await bot.delete_message(callback_query.from_user.id, data.get("bot_message_id"))
                await bot.delete_message(callback_query.from_user.id, data.get("user_message_id"))
                await bot.send_message(callback_query.from_user.id, text=text, reply_markup=get_cancel_menu())
                await SetParserCount.first()
    except Exception as e:
        await state.finish()
        print(e)


@dp.message_handler(state=SetParserCount.all_states)
async def create_lesson_step_two(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        steps_count = data.get("steps_count")
        step_state = await state.get_state()

        if not is_time(message.text) and int(step_state[-1]) == 1:
            text = f"Введите время шаг {step_state[-1]} из {steps_count}"
            await message.answer(text=text, reply_markup=get_cancel_menu())
            await SetParserCount.first()
        elif not is_time(message.text):
            text = f"Введите время шаг {step_state[-1]} из {steps_count}"
            await message.answer(text=text, reply_markup=get_cancel_menu())
            if int(step_state[-1]) == 2:
                return SetParserCount.time_2
            elif step_state[-1] == 3:
                return SetParserCount.time_2
            elif step_state[-1] == 4:
                return SetParserCount.time_4
            elif step_state[-1] == 5:
                return SetParserCount.time_5
            elif step_state[-1] == 6:
                return SetParserCount.time_6

        else:
            if int(steps_count) == int(step_state[-1]):
                key_state = int(step_state[-1])
                await state.update_data({key_state: message.text})
                data = await state.get_data()

                redis_api.delete_time_keys_parsing()
                for key, value in data.items():
                    if isinstance(key, int):
                        redis_api.add_time_parsing(value)

                await state.finish()
                await message.answer(text="Время парсинга установлено", reply_markup=get_admin_keyboard())

            else:
                key_state = int(step_state[-1])
                await state.update_data({key_state: message.text})
                text = f"Введите время шаг {int(step_state[-1]) + 1} из {steps_count}"
                await message.answer(text=text, reply_markup=get_cancel_menu())
                await SetParserCount.next()
    except Exception as e:
        await state.finish()
        print(e)


@dp.message_handler(text="⚙️Настройки")
async def settings(message: types.Message):
    try:
        if message.from_user.id in get_admins() or data_api.get_employees_telegram_ids():
            table = await get_table()
            grps = await get_groups(table)
            pagination = Pagination(message_id=-1, objects=grps.copy(), size=50)
            user_groups = data_api.get_user_groups(message.from_user.id)

            if user_groups is None:
                user_groups = []
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(
                types.KeyboardButton(text='✅ Сохранить'),
                types.KeyboardButton(text='⏪ Главное меню')
            )
            await message.answer('В данном разделе Вы можете настроить группы товаров, используемые в рассылке.',
                                 reply_markup=kb)
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                if obj in user_groups:
                    kb.add(types.InlineKeyboardButton(text=obj + ' ✅',
                                                      callback_data='del_' + str(session) + '_' + obj))
                else:
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
            if await pagination.count() > 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            if len(pagination.objects) != len(user_groups):
                kb.add(
                    types.InlineKeyboardButton(text='💯 Выбрать всё',
                                               callback_data='all_' + str(session))
                )
            else:
                kb.add(
                    types.InlineKeyboardButton(text='❌ Очистить выбор',
                                               callback_data='clear_' + str(session))
                )
            ms = await message.answer('Пожалуйста, выберите группы для рассылки:', reply_markup=kb)
            pagination.message_id = ms.message_id
            storage.data['messages'][ms.message_id] = {'type': 'groups',
                                                       'pagination': pagination,
                                                       'grList': grps.copy(), 'table': table,
                                                       'groups': user_groups.copy(), 'stage': 'groups'}
            storage.data['cm'][ms.chat.id] = ms.message_id
    except Exception as e:
        print(e)


@dp.message_handler(text=["Ссылка доступа"])
async def access_link(message: types.Message):
    user_id = message.chat.id
    if user_id in get_admins():
        code = ''
        while len(code) != 6:
            code += random.choice(symbols)
            if len(code) == 6:
                if code in storage.data['codes'].keys():
                    code = ''
        storage.data['codes'][code] = 'access'
        return await message.answer(text=f'Ссылка доступа успешно сгенерирована:\n\n'
                                         f'https://telegram.me/{BOT_NICKNAME}?start={code}',
                                    reply_markup=get_admin_keyboard())


@dp.message_handler(text=["🏘 Цены по группам"])
async def groups(message: types.Message):
    try:
        user_id = message.chat.id
        if user_id in get_admins() or user_id in data_api.get_employees_telegram_ids():
            table = await get_table()
            grps = await get_groups(table)
            pagination = Pagination(message_id=-1, objects=grps.copy(), size=50)

            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(
                types.KeyboardButton(text='🔎 Мониторинг цен'),
                types.KeyboardButton(text='⏪ Главное меню')
            )
            await message.answer('При выбранном типе мониторинга результаты будут отсортированы по группам товаров.',
                                 reply_markup=kb)
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                kb.add(types.InlineKeyboardButton(text=obj,
                                                  callback_data='set_' + str(session) + '_' + obj))
            if await pagination.count() > 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            kb.add(
                types.InlineKeyboardButton(text='💯 Выбрать всё',
                                           callback_data='all_' + str(session))
            )
            ms = await message.answer('Пожалуйста, выберите группы для мониторинга:', reply_markup=kb)
            pagination.message_id = ms.message_id
            storage.data['messages'][ms.message_id] = {'type': 'groups',
                                                       'pagination': pagination,
                                                       'grList': grps.copy(), 'table': table,
                                                       'groups': [], 'stage': 'groups'}
            storage.data['cm'][ms.chat.id] = ms.message_id
    except Exception as e:
        print(e)


@dp.message_handler(text=["🏠 Цены по товарам"])
async def prods(message: types.Message):
    try:
        user_id = message.chat.id
        if user_id in get_admins() or user_id in data_api.get_employees_telegram_ids():
            table = await get_table()
            grps = await get_groups(table)
            pagination = Pagination(message_id=-1, objects=grps.copy(), size=50)
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(
                types.KeyboardButton(text='🔎 Мониторинг цен'),
                types.KeyboardButton(text='⏪ Главное меню')
            )
            hm = await message.answer('При выбранном типе мониторинга результаты будут отсортированы по названиям товаров.',
                                      reply_markup=kb)
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                kb.add(types.InlineKeyboardButton(text=obj,
                                                  callback_data='set_' + str(session) + '_' + obj))
            if await pagination.count() > 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            ms = await message.answer('Пожалуйста, выберите нужную группу товаров:', reply_markup=kb)
            pagination.message_id = ms.message_id
            storage.data['messages'][ms.message_id] = {'type': 'products', 'pagination': pagination,
                                                       'grList': grps.copy(), 'pList': [],
                                                       'table': table, 'groups': [],
                                                       'products': [], 'stage': 'groups',
                                                       'hm': hm.message_id}
            storage.data['cm'][ms.chat.id] = ms.message_id
    except Exception as e:
        print(e)


async def get_prods(message):
    try:
        user_id = message.chat.id
        if storage.data['cm'].get(user_id) == message.message_id:
            if storage.data['messages'][message.message_id]['groups']:
                storage.data['messages'][message.message_id]['stage'] = 'products'
                prods_ = await get_products(storage.data['messages'][message.message_id]['table'],
                                            storage.data['messages'][message.message_id]['groups'])
                pagination = Pagination(message_id=message.message_id, objects=prods_.copy(), size=50)
                storage.data['messages'][message.message_id]['pagination'] = pagination
                storage.data['messages'][message.message_id]['pList'] = prods_.copy()
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add(
                    types.KeyboardButton(text='🔎 Мониторинг цен'),
                    types.KeyboardButton(text='⏪ Главное меню')
                )
                kb = types.InlineKeyboardMarkup()
                for obj in await pagination.get():
                    if len(obj) > 40:
                        obj = 'Длинное название'
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
                if await pagination.count() > 1:
                    kb.add(
                        types.InlineKeyboardButton(text='Далее ➡',
                                                   callback_data='next_' + str(session))
                    )
                kb.add(
                    types.InlineKeyboardButton(text='💯 Выбрать всё',
                                               callback_data='all_' + str(session))
                )
                await message.edit_text('Пожалуйста, выберите товары для мониторинга:', reply_markup=kb)
            else:
                return False
    except Exception as e:
        print(e)


@dp.callback_query_handler(lambda query: query.data.startswith("set_"))
async def set_(callback_query: types.CallbackQuery):
    try:
        _, s, value = callback_query.data.split("_")
        if int(s) == session and callback_query.message.message_id \
                == storage.data['cm'].get(callback_query.message.chat.id):
            stage = storage.data['messages'][callback_query.message.message_id].get('stage')
            storage.data['messages'][callback_query.message.message_id][stage].append(value)
            if storage.data['messages'][callback_query.message.message_id]['type'] == 'products' and stage == 'groups':
                return await get_prods(callback_query.message)
            pagination = storage.data['messages'][callback_query.message.message_id]['pagination']
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                if obj in storage.data['messages'][callback_query.message.message_id][stage]:
                    kb.add(types.InlineKeyboardButton(text=obj + ' ✅',
                                                      callback_data='del_' + str(session) + '_' + obj))
                else:
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
            if 1 < pagination.page < await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session)),
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session)),

                )
            elif 1 < pagination.page == await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session))
                )
            elif await pagination.count() > 1 and pagination.page == 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            if storage.data['messages'][callback_query.message.message_id]['type'] == 'groups' or stage == 'products':
                if len(pagination.objects) != len(storage.data['messages'][callback_query.message.message_id][stage]):
                    kb.add(
                        types.InlineKeyboardButton(text='💯 Выбрать всё',
                                                   callback_data='all_' + str(session))
                    )
                else:
                    kb.add(
                        types.InlineKeyboardButton(text='❌ Очистить выбор',
                                                   callback_data='clear_' + str(session))
                    )
            await callback_query.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)


@dp.callback_query_handler(lambda query: query.data.startswith("del_"))
async def delete(callback_query: types.CallbackQuery):
    try:
        _, s, value = callback_query.data.split("_")
        if int(s) == session and \
                callback_query.message.message_id == storage.data['cm'].get(callback_query.message.chat.id):
            stage = storage.data['messages'][callback_query.message.message_id].get('stage')
            storage.data['messages'][callback_query.message.message_id][stage].remove(value)
            pagination = storage.data['messages'][callback_query.message.message_id]['pagination']
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                if obj in storage.data['messages'][callback_query.message.message_id][stage]:
                    kb.add(types.InlineKeyboardButton(text=obj + ' ✅', callback_data='del_' + str(session) + '_' + obj))
                else:
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
            if 1 < pagination.page < await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session)),
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session)),
                )
            elif 1 < pagination.page == await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session))
                )
            elif await pagination.count() > 1 and pagination.page == 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            if storage.data['messages'][callback_query.message.message_id]['type'] == 'groups' or stage == 'products':
                if len(pagination.objects) != len(storage.data['messages'][callback_query.message.message_id][stage]):
                    kb.add(
                        types.InlineKeyboardButton(text='💯 Выбрать всё',
                                                   callback_data='all_' + str(session))
                    )
                else:
                    kb.add(
                        types.InlineKeyboardButton(text='❌ Очистить выбор',
                                                   callback_data='clear_' + str(session))
                    )
            return await callback_query.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)

@dp.callback_query_handler(lambda query: query.data.startswith("next_"))
async def next_(callback_query: types.CallbackQuery):
    try:
        _, s = callback_query.data.split("_")
        if int(s) == session and \
                callback_query.message.message_id == storage.data['cm'].get(callback_query.message.chat.id):
            stage = storage.data['messages'][callback_query.message.message_id].get('stage')
            pagination = storage.data['messages'][callback_query.message.message_id]['pagination']
            await pagination.next_page()
            storage.data['messages'][callback_query.message.message_id]['pagination'] = pagination
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                if obj in storage.data['messages'][callback_query.message.message_id][stage]:
                    kb.add(types.InlineKeyboardButton(text=obj + ' ✅',
                                                      callback_data='del_' + str(session) + '_' + obj))
                else:
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
            if 1 < pagination.page < await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session)),
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session)),
                )
            elif pagination.page == await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session))
                )
            if storage.data['messages'][callback_query.message.message_id]['type'] == 'groups' or stage == 'products':
                if len(pagination.objects) != len(storage.data['messages'][callback_query.message.message_id][stage]):
                    kb.add(
                        types.InlineKeyboardButton(text='💯 Выбрать всё',
                                                   callback_data='all_' + str(session))
                    )
                else:
                    kb.add(
                        types.InlineKeyboardButton(text='❌ Очистить выбор',
                                                   callback_data='clear_' + str(session))
                    )
            await callback_query.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)


@dp.callback_query_handler(lambda query: query.data.startswith("back_"))
async def back(callback_query: types.CallbackQuery):
    try:
        _, s = callback_query.data.split("_")
        if int(s) == session and \
                callback_query.message.message_id == storage.data['cm'].get(callback_query.message.chat.id):
            stage = storage.data['messages'][callback_query.message.message_id].get('stage')
            pagination = storage.data['messages'][callback_query.message.message_id]['pagination']
            await pagination.previous_page()
            storage.data['messages'][callback_query.message.message_id]['pagination'] = pagination
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                if obj in storage.data['messages'][callback_query.message.message_id][stage]:
                    kb.add(types.InlineKeyboardButton(text=obj + ' ✅',
                                                      callback_data='del_' + str(session) + '_' + obj))
                else:
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
            if 1 < pagination.page < await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session)),
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session)),
                )
            elif pagination.page == 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            if storage.data['messages'][callback_query.message.message_id]['type'] == 'groups' or stage == 'products':
                if len(pagination.objects) != len(storage.data['messages'][callback_query.message.message_id][stage]):
                    kb.add(
                        types.InlineKeyboardButton(text='💯 Выбрать всё',
                                                   callback_data='all_' + str(session))
                    )
                else:
                    kb.add(
                        types.InlineKeyboardButton(text='❌ Очистить выбор',
                                                   callback_data='clear_' + str(session))
                    )
            await callback_query.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)


@dp.callback_query_handler(lambda query: query.data.startswith("all_"))
async def all_(callback_query: types.CallbackQuery):
    try:
        _, s = callback_query.data.split("_")
        if int(s) == session and \
                callback_query.message.message_id == storage.data['cm'].get(callback_query.message.chat.id):
            stage = storage.data['messages'][callback_query.message.message_id].get('stage')
            if stage == 'groups':
                storage.data['messages'][callback_query.message.message_id]['groups'] \
                    = storage.data['messages'][callback_query.message.message_id]['grList'].copy()
            else:
                storage.data['messages'][callback_query.message.message_id]['products'] \
                    = storage.data['messages'][callback_query.message.message_id]['pList'].copy()
            pagination = storage.data['messages'][callback_query.message.message_id]['pagination']
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                if obj in storage.data['messages'][callback_query.message.message_id][stage]:
                    kb.add(types.InlineKeyboardButton(text=obj + ' ✅',
                                                      callback_data='del_' + str(session) + '_' + obj))
                else:
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
            if 1 < pagination.page < await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session)),
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session)),

                )
            elif 1 < pagination.page == await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session))
                )
            elif await pagination.count() > 1 and pagination.page == 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            if storage.data['messages'][callback_query.message.message_id]['type'] == 'groups' or stage == 'products':
                if len(pagination.objects) != len(storage.data['messages'][callback_query.message.message_id][stage]):
                    kb.add(
                        types.InlineKeyboardButton(text='💯 Выбрать всё',
                                                   callback_data='all_' + str(session))
                    )
                else:
                    kb.add(
                        types.InlineKeyboardButton(text='❌ Очистить выбор',
                                                   callback_data='clear_' + str(session))
                    )
            await callback_query.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)


@dp.callback_query_handler(lambda query: query.data.startswith("clear_"))
async def clear(callback_query: types.CallbackQuery):
    try:
        _, s = callback_query.data.split("_")
        if int(s) == session and \
                callback_query.message.message_id == storage.data['cm'].get(callback_query.message.chat.id):
            stage = storage.data['messages'][callback_query.message.message_id].get('stage')
            storage.data['messages'][callback_query.message.message_id][stage] = []
            pagination = storage.data['messages'][callback_query.message.message_id]['pagination']
            kb = types.InlineKeyboardMarkup()
            for obj in await pagination.get():
                if obj in storage.data['messages'][callback_query.message.message_id][stage]:
                    kb.add(types.InlineKeyboardButton(text=obj + ' ✅',
                                                      callback_data='del_' + str(session) + '_' + obj))
                else:
                    kb.add(types.InlineKeyboardButton(text=obj,
                                                      callback_data='set_' + str(session) + '_' + obj))
            if 1 < pagination.page < await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session)),
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session)),

                )
            elif 1 < pagination.page == await pagination.count():
                kb.add(
                    types.InlineKeyboardButton(text='⬅️ Назад',
                                               callback_data='back_' + str(session))
                )
            elif await pagination.count() > 1 and pagination.page == 1:
                kb.add(
                    types.InlineKeyboardButton(text='Далее ➡',
                                               callback_data='next_' + str(session))
                )
            if storage.data['messages'][callback_query.message.message_id]['type'] == 'groups' or stage == 'products':
                if len(pagination.objects) != len(storage.data['messages'][callback_query.message.message_id][stage]):
                    kb.add(
                        types.InlineKeyboardButton(text='💯 Выбрать всё',
                                                   callback_data='all_' + str(session))
                    )
                else:
                    kb.add(
                        types.InlineKeyboardButton(text='❌ Очистить выбор',
                                                   callback_data='clear_' + str(session))
                    )
            await callback_query.message.edit_reply_markup(reply_markup=kb)
    except Exception as e:
        print(e)


@dp.message_handler(text=["🔎 Мониторинг цен"])
async def price_monitoring(message: types.Message):
    try:
        user_id = message.chat.id
        msgid = storage.data['cm'].get(user_id)

        if msgid:
            if storage.data['messages'][msgid]['type'] == 'groups':
                if storage.data['messages'][msgid]['groups']:
                    products = await get_by_groups(storage.data['messages'][msgid]['table'],
                                                   storage.data['messages'][msgid]['groups'])
                else:
                    products = None
            else:
                if storage.data['messages'][msgid]['products']:
                    products = await get_by_products(storage.data['messages'][msgid]['table'],
                                                     storage.data['messages'][msgid]['groups'],
                                                     storage.data['messages'][msgid]['products'])
                else:
                    products = None
            if products:
                await bot.delete_message(chat_id=user_id, message_id=msgid)
                if user_id in get_admins():
                    reply_markup = get_admin_keyboard()
                else:
                    reply_markup = get_user_keyboard()

                await bot.send_message(chat_id=user_id,
                                       text=f'Количество результатов: {len(products)}\n'
                                            f'*Полученные результаты:*\n',
                                       reply_markup=reply_markup,
                                       parse_mode='markdown')
                for obj in products:
                    if not obj.get('roz') and not obj.get('opt'):
                        continue
                    msg = f'⏰ {datetime.now().strftime("%d/%m/%Y %H:%M")}\n' \
                          f'\nГруппа товара: <b>{obj["group"]}</b>' \
                          f'\nНазвание товара: <b>{obj["product"]}</b>\n' \
                          f'\n<a href=\"{obj["roz"]["link"]}\">Наша розничная цена:</a> <b>{obj["roz"]["price"]} грн.</b>' \
                          f'\n<a href=\"{obj["opt"]["link"]}\">Наша оптовая цена:</a> <b>{obj["opt"]["price"]} грн.</b>\n' \
                          f'\n<i>Цены конкурентов:</i>\n'
                    conc = ''
                    for key, value in obj.items():
                        if key not in ['group', 'product', 'roz', 'opt', 'image']:
                            prc = ''
                            roz = obj[key].get('roz')
                            opt = obj[key].get('opt')
                            if roz:
                                if roz.get('price'):
                                    if obj['roz']['price'] == roz['price']:
                                        prc += \
                                            f'<a href=\"{roz.get("link")}\">' \
                                            f'Розничная цена:</a> ⬜ <b>{roz["price"]} грн.</b>\n'
                                    elif obj['roz']['price'] < roz['price']:
                                        prc += \
                                            f'<a href=\"{roz.get("link")}\">' \
                                            f'Розничная цена:</a> 🟩 <b>{roz["price"]} грн.</b>\n'
                                    else:
                                        prc += f'<a href=\"{roz.get("link")}\">' \
                                               f'Розничная цена:</a> 🟥 <b>{roz["price"]} грн.</b>\n'
                            if opt:
                                if opt.get('price'):
                                    if obj['opt']['price'] == opt['price']:
                                        prc += f'<a href=\"{opt.get("link")}\">' \
                                               f'Оптовая цена:</a> ⬜ <b>{opt["price"]} грн.</b>\n'
                                    elif obj['opt']['price'] < opt['price']:
                                        prc += f'<a href=\"{opt.get("link")}\">' \
                                               f'Оптовая цена:</a> 🟩 <b>{opt["price"]} грн.</b>\n'
                                    else:
                                        prc += f'<a href=\"{opt.get("link")}\">' \
                                               f'Оптовая цена:</a> 🟥 <b>{opt["price"]} грн.</b>\n'
                            if len(prc) != 0:
                                conc += f'\nСайт: {key}\n' + prc
                    if not conc:
                        msg += '\nЦены конкурентов не обнаружены.\n'
                    else:
                        msg += conc
                    if obj['image'] is not None:
                        if len(msg) <= 2048:
                            await bot.send_photo(chat_id=user_id, caption=msg,
                                                 parse_mode='html', photo=obj['image'])
                        else:
                            await bot.send_message(chat_id=user_id, text=msg,
                                                   disable_web_page_preview=True, parse_mode='html')
                            await bot.send_photo(chat_id=user_id, photo=obj['image'])
                    else:
                        await bot.send_message(chat_id=user_id, text=msg,
                                               disable_web_page_preview=True,
                                               parse_mode='html')

                    await asyncio.sleep(0.5)
                if msgid in storage.data['messages'].keys():
                    storage.data['messages'].pop(msgid)
                storage.data['cm'].pop(user_id)
    except Exception as e:
        print(e)

async def mailing_user_price_monitoring():
    try:

        employees_mailing_list = data_api.get_employees_product_lists()
        table = await get_table()

        for user_id, mailing_data_list in employees_mailing_list:

            if mailing_data_list:
                products = await get_by_groups(table, mailing_data_list)
            else:
                products = None

            if products:
                await bot.send_message(chat_id=user_id,
                                       text=f'Количество результатов: {len(products)}\n'
                                            f'*Полученные результаты:*\n',
                                       parse_mode='markdown')
                for obj in products:
                    if not obj.get('roz') and not obj.get('opt'):
                        continue
                    msg = f'⏰ {datetime.now().strftime("%d/%m/%Y %H:%M")}\n' \
                          f'\nГруппа товара: <b>{obj["group"]}</b>' \
                          f'\nНазвание товара: <b>{obj["product"]}</b>\n' \
                          f'\n<a href=\"{obj["roz"]["link"]}\">Наша розничная цена:</a> <b>{obj["roz"]["price"]} грн.</b>' \
                          f'\n<a href=\"{obj["opt"]["link"]}\">Наша оптовая цена:</a> <b>{obj["opt"]["price"]} грн.</b>\n' \
                          f'\n<i>Цены конкурентов:</i>\n'
                    conc = ''
                    for key, value in obj.items():
                        if key not in ['group', 'product', 'roz', 'opt', 'image']:
                            prc = ''
                            roz = obj[key].get('roz')
                            opt = obj[key].get('opt')
                            if roz:
                                if roz.get('price'):
                                    if obj['roz']['price'] == roz['price']:
                                        prc += \
                                            f'<a href=\"{roz.get("link")}\">' \
                                            f'Розничная цена:</a> ⬜ <b>{roz["price"]} грн.</b>\n'
                                    elif obj['roz']['price'] < roz['price']:
                                        prc += \
                                            f'<a href=\"{roz.get("link")}\">' \
                                            f'Розничная цена:</a> 🟩 <b>{roz["price"]} грн.</b>\n'
                                    else:
                                        prc += f'<a href=\"{roz.get("link")}\">' \
                                               f'Розничная цена:</a> 🟥 <b>{roz["price"]} грн.</b>\n'
                            if opt:
                                if opt.get('price'):
                                    if obj['opt']['price'] == opt['price']:
                                        prc += f'<a href=\"{opt.get("link")}\">' \
                                               f'Оптовая цена:</a> ⬜ <b>{opt["price"]} грн.</b>\n'
                                    elif obj['opt']['price'] < opt['price']:
                                        prc += f'<a href=\"{opt.get("link")}\">' \
                                               f'Оптовая цена:</a> 🟩 <b>{opt["price"]} грн.</b>\n'
                                    else:
                                        prc += f'<a href=\"{opt.get("link")}\">' \
                                               f'Оптовая цена:</a> 🟥 <b>{opt["price"]} грн.</b>\n'
                            if len(prc) != 0:
                                conc += f'\nСайт: {key}\n' + prc
                    if not conc:
                        msg += '\nЦены конкурентов не обнаружены.\n'
                    else:
                        msg += conc
                    if obj['image'] is not None:
                        if len(msg) <= 2048:
                            await bot.send_photo(chat_id=user_id, caption=msg,
                                                 parse_mode='html', photo=obj['image'])
                        else:
                            await bot.send_message(chat_id=user_id, text=msg,
                                                   disable_web_page_preview=True, parse_mode='html')
                            await bot.send_photo(chat_id=user_id, photo=obj['image'])
                    else:
                        await bot.send_message(chat_id=user_id, text=msg,
                                               disable_web_page_preview=True,
                                               parse_mode='html')

                    await asyncio.sleep(0.5)
    except Exception as e:
        print(e)


@dp.message_handler(text=["⏪ Главное меню"])
async def exit_(message: types.Message):
    try:
        user_id = message.chat.id
        msg = storage.data['cm'].get(user_id)
        if msg:
            if msg in storage.data['messages'].keys():
                storage.data['messages'].pop(msg)
            storage.data['cm'].pop(user_id)
            await bot.delete_message(chat_id=user_id, message_id=msg)
        if user_id in get_admins():
            reply_markup = get_admin_keyboard()
        else:
            reply_markup = get_user_keyboard()

        string = 'Добро пожаловать в гланое меню бота!\nПожалуйста, выберите одно из доступных действий:'
        await bot.send_message(chat_id=user_id, text=string, reply_markup=reply_markup)
    except Exception as e:
        print(e)


@dp.message_handler(text=["✅ Сохранить"])
async def save(message: types.Message):
    try:
        user_id = message.chat.id
        msg = storage.data['cm'].get(user_id)
        if msg:
            list_groups_product = storage.data['messages'][msg]['groups']
            data_api.update_product_list_employee(message=message, list_groups_product=list_groups_product)
            if msg in storage.data['messages'].keys():
                storage.data['messages'].pop(msg)
            storage.data['cm'].pop(user_id)

            await bot.edit_message_text(chat_id=user_id, message_id=msg, text='Настройки успешно сохранены!')

            text = 'Добро пожаловать в гланое меню бота!\nПожалуйста, выберите одно из доступных действий:'
            if user_id in get_admins():
                await bot.send_message(chat_id=user_id, text=text, reply_markup=get_admin_keyboard())
            else:
                await bot.send_message(chat_id=user_id, text=text, reply_markup=get_user_keyboard())
    except Exception as e:
        print(e)


@dp.message_handler(text="➕ Добавить таблицу")
async def add_table_start(message: types.Message):
    if message.from_user.id in get_admins():
        await message.answer("Добавьте новый файл для обработки в формате xlsx", reply_markup=get_cancel_menu())
        await AddTable.first()


@dp.message_handler(content_types=['document'], state=AddTable.file)
async def add_table_file(message: types.Message, state: FSMContext):
    try:
        if message.from_user.id in get_admins():

            file_name = message.document.file_name
            type_file = file_name.split('.')[-1]

            if type_file != 'xlsx':
                await message.answer("Данный формат файла не поддерживается, работаем только с xlsx",
                                     reply_markup=get_admin_keyboard())
            elif os.path.exists("temp/database_result.xlsx"):
                await message.answer("Сейчас происходит парсинг по расписанию, попробуйте добавить файл через 10 минут",
                                     reply_markup=get_admin_keyboard())

            else:
                try:
                    src = f'temp/database.xlsx'
                    await message.document.download(destination_file=src)
                    add_table.delay()
                    await message.answer("Файл добавлен в очередь для обработки", reply_markup=get_admin_keyboard())
                    await state.finish()

                except Exception as e:
                    text = "Что то пошло не так\nОшибка\n" + str(e)
                    await bot.send_message(message.from_user.id, text, reply_markup=get_admin_keyboard())
    except Exception as e:
        await state.finish()
        print(e)


@dp.message_handler(ChatTypeFilter(chat_type=ChatType.PRIVATE), Text("❌ Удалить сотрудника"))
async def bind_admin_group(message: types.Message, state: FSMContext):
    try:
        if message.from_user.id in get_admins():
            reply_markup = get_employees_for_bind()
            if reply_markup:
                msg = await bot.send_message(message.from_user.id,
                                       text="Какого сотрудника удалить из базы?",
                                       reply_markup=reply_markup)
                await state.update_data(message_id=msg.message_id)
                await DeleteEmployee.first()
            else:
                await bot.send_message(message.from_user.id,
                                       text="Сотрудников в базе пока нет",
                                       reply_markup=get_admin_keyboard())
    except Exception as e:
        print(e)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('u_a_'), state=DeleteEmployee.user_id)
async def delete_employee_finish(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = callback_query.data[4:]
        if user_id == "cancel":
            reply_markup = get_admin_keyboard()
            await state.finish()
            await bot.delete_message(chat_id=callback_query.from_user.id, message_id=data.get("message_id"))
            await bot.send_message(callback_query.from_user.id, text="Операция отменена", reply_markup=reply_markup)
        else:

            if data_api.delete_employee(user_id):
                await bot.send_message(callback_query.from_user.id,
                                       text="Сотрудник успешно удалён",
                                       reply_markup=get_admin_keyboard())
            else:
                await bot.send_message(callback_query.from_user.id,
                                       text="Что то пошло не так, попробуйте ещё раз",
                                       reply_markup=get_admin_keyboard())
            await bot.delete_message(chat_id=callback_query.from_user.id, message_id=data.get("message_id"))
            await state.finish()
    except Exception as e:
        await state.finish()
        print(e)


@dp.message_handler(text="🗒 Отчет")
async def add_table_start(message: types.Message):
    if message.from_user.id in get_admins():
        if os.path.exists("temp/database_result.xlsx"):
            await message.answer("Сейчас происходит парсинг по расписанию, попробуйте запросить отчет через 10 минут",
                                 reply_markup=get_admin_keyboard())
        else:
            with open('tables/database_result.xlsx', 'rb') as file:
                await bot.send_document(chat_id=message.from_user.id,
                                        document=file)


async def start_parsing():
    if redis_api.check_time_parsing():
        regular_parsing.delay()


if __name__ == '__main__':
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f__:
            f__.write(json.dumps({"access": [], "admins": [], "lsid": 0, "usergroups": {}}))

    storage.data['codes'] = {}
    storage.data['messages'] = {}
    storage.data['cm'] = {}

    session = get_lsid() + 1
    set_lsid(session)

    scheduler.add_job(func=start_parsing, trigger='cron', hour='7', minute='15')
    scheduler.add_job(func=mailing_user_price_monitoring, trigger='cron', hour='8')

    scheduler.add_job(func=start_parsing, trigger='cron', hour='15', minute='15')
    scheduler.add_job(func=mailing_user_price_monitoring, trigger='cron', hour='16')

    scheduler.add_job(func=start_parsing, trigger='interval', seconds=60)

    scheduler.start()
    executor.start_polling(dispatcher=dp, skip_updates=True)
