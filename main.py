import json
import asyncio
import logging
import sys
from random import randint

from dotenv import dotenv_values

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    BotCommand,
    FSInputFile
)

from keyboards import EXAM_TYPE_KEYBOARD, CHECKING_STOP_TEST_KEYBOARD, SOLVE_KEYBOARD


config = dotenv_values(".env")
TOKEN = config["TOKEN"]
form_router = Router()

with open("tests.json", 'r', encoding='utf-8') as file:
    TESTS: dict[str, list[list[dict[str, str]]]] = json.load(file)

HELLO_TEXT = """👋 Привет!
Ты в умном боте для подготовки к ЕГЭ и ОГЭ математике.

Здесь ты сможешь:
✅ Проверить свои ответы.
✅ Узнать правильное решение.
✅ Получить подсказку, если что-то пошло не так.

🚀 Просто введи номер задания или отправь свой ответ — бот всё проверит!
И помни: каждая ошибка — это шаг к 100 баллам.

Готов проверить себя? Погнали! 🎯
"""


BOT_COMMANDS = [
    BotCommand(command="start", description="Start bot"),
    BotCommand(command="solve", description="Start solving tasks")
]


async def show_results(message: Message, state: FSMContext) -> None:
    text = "Результаты:\n\n"

    data = await state.get_data()
    exam_type = data.get("exam_type", "ege")
    variant_idx = data["variant_idx"]
    variant = TESTS[exam_type][variant_idx]

    user_answers = data.get("answers", [])
    right_answers = [task["answer"] for task in variant]

    cnt_right_solutions = 0

    for idx, (user_answer, right_answer) in enumerate(zip(user_answers, right_answers)):
        cnt_right_solutions += user_answer == right_answer
        text += f"{idx + 1}) {"+" if user_answer == right_answer else "-"}\n"

    text += f"\nВаш результат: {cnt_right_solutions}/{len(user_answers)}"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())


async def show_task(message: Message, task: dict[str, str], task_id: int) -> None:
    if "path" in task:
        photo = FSInputFile(task["path"])
        await message.answer_photo(
            photo,
            caption=f"ЗАДАНИЕ №{task_id}\n\n{task['text']}",
            reply_markup=SOLVE_KEYBOARD
        )
    else:
        await message.answer(
            f"ЗАДАНИЕ №{task_id}\n\n{task['text']}",
            reply_markup=SOLVE_KEYBOARD
        )


class Form(StatesGroup):
    choosing_exam = State()  # Новое состояние для выбора типа экзамена
    solving_tasks = State()
    stopping_solving = State()


@form_router.message(CommandStart())
async def command_start(message: Message) -> None:
    await message.answer(
        HELLO_TEXT,
        reply_markup=ReplyKeyboardRemove()
    )


@form_router.message(Command("solve"))
async def command_solve(message: Message, state: FSMContext) -> None:
    if await state.get_state() == Form.solving_tasks:
        await message.answer(
            "Чтобы начать решать новый вариант, закончите старый.\n"
            "Для прекращения решения теста нажмите \"Стоп\"."
        )
        return

    await state.set_state(Form.choosing_exam)
    await message.answer(
        "Выберите тип экзамена:",
        reply_markup=EXAM_TYPE_KEYBOARD
    )


@form_router.message(Form.choosing_exam, F.text.casefold().in_(["огэ", "егэ"]))
async def process_exam_choice(message: Message, state: FSMContext) -> None:
    exam_type = "oge" if message.text.casefold() == "огэ" else "ege"
    await state.update_data(exam_type=exam_type)

    variant_idx = randint(0, len(TESTS[exam_type]) - 1)
    await message.answer(f"ВАРИАНТ №{variant_idx + 1}", reply_markup=ReplyKeyboardRemove())

    await state.set_state(Form.solving_tasks)
    await state.update_data(variant_idx=variant_idx, task_idx=0)

    variant = TESTS[exam_type][variant_idx]
    await show_task(message, variant[0], 1)


@form_router.message(Form.choosing_exam)
async def process_unknown_exam_type(message: Message) -> None:
    await message.answer("Пожалуйста, выберите тип экзамена, используя кнопки ниже.")


@form_router.message(F.text.casefold() == "стоп", Form.solving_tasks)
async def process_stop_first(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.stopping_solving)
    await message.answer(
        "Вы действительно хотите прекратить решение теста?",
        reply_markup=CHECKING_STOP_TEST_KEYBOARD
    )


@form_router.message(F.text.casefold() == "стоп", Form.stopping_solving)
async def process_stop_final(message: Message, state: FSMContext) -> None:
    await show_results(message, state)
    await state.set_state(None)
    await state.update_data(answers=[], task_idx=0)


@form_router.message(F.text.casefold() == "стоп", default_state)
async def process_stop_undefined(message: Message) -> None:
    await message.answer("Чтобы оставить решение варианта, сначала нужно его начать.")


@form_router.message(F.text.casefold() == "продолжить", Form.stopping_solving)
async def process_continue_solving(message: Message, state: FSMContext) -> None:
    await message.answer("Решение заданий успешно восставновлено.", reply_markup=SOLVE_KEYBOARD)
    await state.set_state(Form.solving_tasks)


@form_router.message(Form.solving_tasks)
async def process_answer_task(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    exam_type = data.get("exam_type", "ege")
    answer = message.text
    answers = data.get("answers", []) + [answer]
    task_idx = data["task_idx"] + 1
    variant_idx = data["variant_idx"]
    variant = TESTS[exam_type][variant_idx]

    await state.update_data(answers=answers, task_idx=task_idx)

    if task_idx == len(variant):
        await show_results(message, state)
        await state.set_state(None)
        await state.update_data(answers=[], task_idx=0)
    else:
        next_task = variant[task_idx]
        await show_task(message, next_task, task_idx + 1)

@form_router.message()
async def process_unknown_command(message: Message):
    await message.answer("Неизвестная команда.")


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands(commands=BOT_COMMANDS)

    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout)
    asyncio.run(main())
