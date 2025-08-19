from aiogram.fsm.state import StatesGroup, State

class BotStates(StatesGroup):
    START = State()
    MAIN_MENU = State()
    BALANCE_MENU = State()
    TARIFFS_LIST = State()