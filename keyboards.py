from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


EXAM_TYPE_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ОГЭ"), KeyboardButton(text="ЕГЭ")]
    ],
    resize_keyboard=True
)

SOLVE_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Стоп")]],
    resize_keyboard=True
)

CHECKING_STOP_TEST_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Стоп"), KeyboardButton(text="Продолжить")]],
    resize_keyboard=True
)
