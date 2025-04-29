import json
import asyncio
import logging
import sys
from random import randint

from dotenv import dotenv_values

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    BotCommand
)

from keyboards import SOLVE_KEYBOARD_MARKUP, CHECKING_STOP_TEST_KEYBOARD_MARKUP

config = dotenv_values(".env")


form_router = Router()


TOKEN = config["TOKEN"]


with open("tests.json", 'r', encoding='utf-8') as file:
    TESTS: list[list[dict[str, str]]] = json.load(file)


BOT_COMMANDS = [
    BotCommand(command="start", description="Start bot"),
    BotCommand(command="solve", description="Start solving tasks")
]


async def show_results(message: Message, state: FSMContext) -> None:
    text = ""

    variant_idx = await state.get_value("variant_idx")
    variant = TESTS[variant_idx]

    user_answers = await state.get_value("answers", [])
    right_answers = [task["answer"] for task in variant]

    print(user_answers)
    print(right_answers)

    cnt_right_solutions = 0

    for idx, (user_answer, right_answer) in enumerate(zip(user_answers, right_answers)):
        text += f"№{idx + 1}:  "
        verdict = "❌"
        if user_answer == right_answer:
            cnt_right_solutions += 1
            verdict = "✅"

        text += f"{verdict}\nВаш ответ: {user_answer}\nПравильный ответ: {html.bold(right_answer)}\n\n"

    text += f"Результат: {cnt_right_solutions}/{len(user_answers)}"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())


class Form(StatesGroup):
    solving_tasks = State()
    stopping_solving = State()


@form_router.message(CommandStart())
async def command_start(message: Message) -> None:
    name = message.from_user.first_name
    await message.answer(
        f"Привет, {name}! Это бот для тренировки заданий формата ЕГЭ по русскому языку. Чтобы приступить к решению заданий, испльзуй команду \solve.",
        reply_markup=ReplyKeyboardRemove()
    )


@form_router.message(Command("solve"))
async def command_solve(message: Message, state: FSMContext) -> None:
    if await state.get_state() == Form.solving_tasks:
        await message.answer("Чтобы начать решать новый вариант, закончите старый.\nДля прекращения решения теста нажмите \"Стоп\".")
        return

    variant_idx = randint(0, len(TESTS) - 1)
    await message.answer(f"ВАРИАНТ №{variant_idx + 1}")

    await state.set_state(Form.solving_tasks)
    await state.update_data(variant_idx=variant_idx, task_idx=0)

    await message.answer(
        f"ЗАДАНИЕ №1\n\n{TESTS[variant_idx][0]["text"]}",
        reply_markup=SOLVE_KEYBOARD_MARKUP
    )


@form_router.message(F.text.casefold() == "стоп", Form.solving_tasks)
async def process_stop_first(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.stopping_solving)
    await message.answer(
        "Вы действительно хотите прекратить решение теста?",
        reply_markup=CHECKING_STOP_TEST_KEYBOARD_MARKUP
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
    await message.answer("Решение заданий успешно восставновлено.", reply_markup=SOLVE_KEYBOARD_MARKUP)
    await state.set_state(Form.solving_tasks)


@form_router.message(Form.solving_tasks)
async def process_answer_task(message: Message, state: FSMContext) -> None:
    data: dict = await state.get_data()

    answer = message.text
    answers = data.get("answers", []) + [answer]

    task_idx = data["task_idx"] + 1

    variant_idx = data["variant_idx"]
    variant = TESTS[variant_idx]

    data["answers"] = answers
    data["task_idx"] = task_idx

    await state.set_data(data)

    if task_idx == len(variant):
        await show_results(message, state)

        await state.set_state(None)
        data["answers"] = []
        data["task_idx"] = 0

        await state.set_data(data)
    else:
        task_text = variant[task_idx]["text"]
        await message.answer(f"ЗАДАНИЕ №{task_idx + 1}\n\n" + task_text)



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
