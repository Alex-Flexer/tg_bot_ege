from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)


EXAM_TYPE_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ОГЭ"), KeyboardButton(text="ЕГЭ")]
    ],
    resize_keyboard=True
)

FIRST_CHECKING_STOP_TEST_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Стоп")]],
    resize_keyboard=True
)

FINAL_CHECKING_STOP_TEST_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Стоп"), KeyboardButton(text="Продолжить")]],
    resize_keyboard=True
)


START_INLINE_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="ОГЭ", callback_data="start_oge"),
         InlineKeyboardButton(text="ЕГЭ", callback_data="start_ege")],
        [InlineKeyboardButton(text="Контакты", callback_data="start_contacts")]
    ]
)

EGE_INLINE_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="ЕГЭ", callback_data="start_ege")]
    ]
)

OGE_INLINE_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="ОГЭ", callback_data="start_oge")]
    ]
)

EXAM_TYPE_INLINE_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="ОГЭ", callback_data="start_oge"),
         InlineKeyboardButton(text="ЕГЭ", callback_data="start_ege")]
    ]
)
