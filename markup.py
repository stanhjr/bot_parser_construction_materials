from aiogram import Bot as AiogramBot, executor, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from models.data_api import data_api


def get_admin_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text='Ссылка доступа'),
           types.KeyboardButton(text='🗒 Отчет'))
    kb.add(types.KeyboardButton(text='🕘 Время Парсинга'),
           types.KeyboardButton(text='⚙️Настройки')),
    kb.add(types.KeyboardButton(text='🏘 Цены по группам'),
           types.KeyboardButton(text='🏠 Цены по товарам'))
    kb.add(types.KeyboardButton(text='➕ Добавить таблицу'),
           types.KeyboardButton(text='❌ Удалить сотрудника'))

    return kb


def get_user_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text='🏘 Цены по группам'),
           types.KeyboardButton(text='🏠 Цены по товарам'))
    kb.add(types.KeyboardButton(text='⚙️Настройки'))
    return kb


def get_cancel_menu():
    cancel_menu = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cancel_button = KeyboardButton("❌Отмена")
    cancel_menu.add(cancel_button)
    return cancel_menu


def get_count_of_parsing_keyboard():
    inline_kb_full = InlineKeyboardMarkup(row_width=2)
    for num in range(1, 7):
        inline_kb_full.add(InlineKeyboardButton(str(num), callback_data=f"pars_{num}"))
    inline_kb_full.add(InlineKeyboardButton("❌Отмена", callback_data="pars_cancel"))
    return inline_kb_full


def get_employees_for_bind():
    employees = data_api.get_employees_first_name()
    if employees:
        inline_kb_full = InlineKeyboardMarkup(row_width=2)
        for user_id, user_first_name in employees:
            inline_kb_full.add(InlineKeyboardButton(user_first_name, callback_data=f"u_a_{user_id}"))
        inline_kb_full.add(InlineKeyboardButton("❌Отмена", callback_data="u_a_cancel"))
        return inline_kb_full


