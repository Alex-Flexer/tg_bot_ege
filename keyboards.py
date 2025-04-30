from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


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


START_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="ОГЭ", callback_data="start_oge"),
         InlineKeyboardButton(text="ЕГЭ", callback_data="start_ege")]
    ]
)
