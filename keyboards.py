from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


SOLVE_KEYBOARD_MARKUP =\
    ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Стоп")]],
        resize_keyboard=True
    )

CHECKING_STOP_TEST_KEYBOARD_MARKUP =\
    ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Стоп"), KeyboardButton(text="Продолжить")]],
        resize_keyboard=True
    )
