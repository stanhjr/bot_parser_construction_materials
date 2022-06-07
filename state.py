from aiogram.dispatcher.filters.state import StatesGroup, State


class SetParserCount(StatesGroup):
    time_1 = State()
    time_2 = State()
    time_3 = State()
    time_4 = State()
    time_5 = State()
    time_6 = State()


class AddTable(StatesGroup):
    file = State()


class DeleteEmployee(StatesGroup):
    user_id = State()






