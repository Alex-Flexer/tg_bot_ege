import json
import asyncio
import logging
import sys
from os.path import join
from os import listdir

from dotenv import dotenv_values

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    BotCommand,
    FSInputFile,
    CallbackQuery
)

from keyboards import (
    FINAL_CHECKING_STOP_TEST_KEYBOARD,
    FIRST_CHECKING_STOP_TEST_KEYBOARD,
    EXAM_TYPE_KEYBOARD,
    START_INLINE_KEYBOARD,
    EGE_INLINE_KEYBOARD,
    OGE_INLINE_KEYBOARD,
    EXAM_TYPE_INLINE_KEYBOARD
)

BOT_COMMANDS = [
    BotCommand(command="start", description="Start bot"),
    BotCommand(command="solve", description="Start solving tasks"),
    BotCommand(command="contacts", description="Get contacts")
]

config = dotenv_values(".env")
TOKEN = config["TOKEN"]

form_router = Router()


with open("answers.json", 'r', encoding='utf-8') as file:
    ANSWERS: dict[str, list[list[str]]] = json.load(file)


HELLO_TEXT = """👋 Привет!
Ты в умном боте для подготовки к ЕГЭ и ОГЭ математике.

Здесь ты сможешь:
✅ Проверить свои ответы.
✅ Получишь консультацию через кнопку «контакты»

🚀 Просто введи номер варианта и отправь свой ответ — бот всё проверит!
И помни: каждая ошибка — это шаг к 100 баллам.

Готов проверить себя? Погнали! 🎯
"""

CONTACS_TEXT = """Поддержка:

Присоединяйтесь к нашему Telegram-каналу:
@matnas7

💬 Если у вас есть вопросы или вам нужна помощь:
@NikitaAlekseevichh
"""


async def show_results(message: Message, state: FSMContext) -> None:
    text = "Результат:\n\n"

    data = await state.get_data()

    exam_type = data["exam_type"]
    variant_idx = data["variant_idx"]
    task_idx = data["task_idx"]

    if task_idx < 5 and exam_type == "oge":
        task_img = data["task_img"]
        await task_img.delete()

    user_answers: list[str] = data.get("answers", [])
    right_answers: list[str] = ANSWERS[exam_type][variant_idx]

    cnt_right_solutions = 0

    for idx, (user_answer, right_answer) in enumerate(zip(user_answers, right_answers)):
        verdict = user_answer.replace(".", ",").replace(" ", "") == right_answer
        cnt_right_solutions += verdict
        text += f"{idx + 1}) {"+" if verdict else "-"}\n"

    text += f"\nВаш результат: {cnt_right_solutions}/{len(user_answers)}"

    if cnt_right_solutions == len(right_answers):
        photo = FSInputFile("./images/perfect_img.jpg")
        await message.answer_photo(
            photo,
            text,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(text, reply_markup=ReplyKeyboardRemove())

    await message.answer(
        "Хотите продолжить подготовку?",
        reply_markup=(
            EXAM_TYPE_INLINE_KEYBOARD if len(user_answers) != len(right_answers)
            else (EGE_INLINE_KEYBOARD if exam_type == "ege" else OGE_INLINE_KEYBOARD)
        )
    )


async def show_task(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    exam_type = data["exam_type"]
    variant_idx = data["variant_idx"]
    task_idx = data["task_idx"]

    photo_path = join(".", exam_type, str(variant_idx), str(task_idx) + ".png")
    photo = FSInputFile(photo_path)
    caption = f"ЗАДАНИЕ №{task_idx + 1}"

    if task_idx > 0:
        last_msg = data["last_msg"]
        await last_msg.delete()

    if task_idx == 5 and exam_type == "oge":
        task_img = data["task_img"]
        await task_img.delete()

    last_msg = await message.answer_photo(
        photo,
        caption=caption,
        reply_markup=FIRST_CHECKING_STOP_TEST_KEYBOARD
    )
    await state.update_data(last_msg=last_msg)


class Form(StatesGroup):
    choosing_exam = State()
    choosing_variant = State()
    solving_tasks = State()
    stopping_solving = State()


@form_router.message(CommandStart())
async def command_start(message: Message) -> None:
    photo = FSInputFile("./images/start_img.jpg")
    await message.answer_photo(
        photo,
        HELLO_TEXT,
        reply_markup=START_INLINE_KEYBOARD
    )


@form_router.message(Command("solve"))
async def command_solve(message: Message, state: FSMContext) -> None:
    if await state.get_state() == Form.solving_tasks:
        await message.answer(
            "Чтобы начать новый вариант, закончите текущий.\n"
            "Для прекращения решения нажмите \"Стоп\"."
        )
        return

    await state.set_state(Form.choosing_exam)
    await message.answer(
        "Выберите тип экзамена:",
        reply_markup=EXAM_TYPE_KEYBOARD,
    )


@form_router.message(Command("contacts"))
async def command_contacts(message: Message) -> None:
    await message.answer(CONTACS_TEXT)


@form_router.message(F.text.casefold() == "стоп", or_f(Form.solving_tasks, Form.choosing_variant))
async def process_stop_first(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.stopping_solving)
    await message.answer(
        "Вы действительно хотите прекратить решение теста?",
        reply_markup=FINAL_CHECKING_STOP_TEST_KEYBOARD
    )


@form_router.message(F.text.casefold() == "стоп", Form.stopping_solving)
async def process_stop_final(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Тест приостановлен.",
        reply_markup=EXAM_TYPE_INLINE_KEYBOARD
    )

    if await state.get_value("variant_idx") is not None:
        await show_results(message, state)

    await state.set_state(None)
    await state.update_data(answers=[], task_idx=None, variant_idx=None, task_img=None)


@form_router.message(F.text.casefold() == "стоп", default_state)
async def process_stop_undefined(message: Message) -> None:
    await message.answer("Чтобы оставить решение варианта, сначала нужно его начать.")


@form_router.message(F.text.casefold() == "продолжить", Form.stopping_solving)
async def process_continue_solving(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Решение заданий успешно восставновлено.",
        reply_markup=FIRST_CHECKING_STOP_TEST_KEYBOARD
    )
    await state.set_state(Form.solving_tasks)


@form_router.callback_query(F.data.startswith("start_"))
async def handle_start_buttons(callback: CallbackQuery, state: FSMContext):
    if callback.data == "start_contacts":
        await callback.message.answer(CONTACS_TEXT)
    else:
        exam_type = "oge" if callback.data == "start_oge" else "ege"
        await state.update_data(exam_type=exam_type)

        await state.set_state(Form.choosing_variant)

        max_variants = len(listdir(f"./{exam_type}"))
        await callback.message.answer(
            f"Введите номер варианта (от 1 до {max_variants}):",
            reply_markup=FIRST_CHECKING_STOP_TEST_KEYBOARD
        )
    await callback.answer()


@form_router.message(Form.choosing_exam, F.text.casefold().in_(["огэ", "егэ"]))
async def process_exam_choice(message: Message, state: FSMContext) -> None:
    exam_type = "oge" if message.text.casefold() == "огэ" else "ege"

    await state.update_data(exam_type=exam_type)
    await state.set_state(Form.choosing_variant)

    max_variants = len(listdir(f"./{exam_type}"))
    await message.answer(
        f"Введите номер варианта (от 1 до {max_variants}):",
        reply_markup=FIRST_CHECKING_STOP_TEST_KEYBOARD
    )


@form_router.message(Form.choosing_exam)
async def process_unknown_exam_type(message: Message) -> None:
    await message.answer("Пожалуйста, выберите тип экзамена, используя кнопки ниже.")


@form_router.message(Form.choosing_variant, F.text.regexp(r'^\d+$'))
async def process_variant_number(message: Message, state: FSMContext) -> None:
    variant_number = int(message.text)

    exam_type = await state.get_value("exam_type")
    max_variants = len(listdir(f"./{exam_type}"))

    if 1 <= variant_number <= max_variants:
        variant_idx = variant_number - 1
        await state.update_data(
            variant_idx=variant_idx,
            task_idx=0,
            answers=[]
        )
        await state.set_state(Form.solving_tasks)
        await message.answer(f"ВАРИАНТ №{variant_number}", reply_markup=ReplyKeyboardRemove())
        if exam_type == "oge":
            task_img = await message.answer_photo(FSInputFile(f"./oge/{variant_idx}/img.png"))
            await state.update_data(task_img=task_img)

        await show_task(message, state)
    else:
        await message.answer(f"Пожалуйста, введите число от 1 до {max_variants}")


@form_router.message(Form.choosing_variant)
async def process_invalid_variant_number(message: Message, state: FSMContext) -> None:
    exam_type = await state.get_value("exam_type")
    max_variants = len(listdir(f"./{exam_type}"))
    await message.answer(f"Пожалуйста, введите число от 1 до {max_variants}")


@form_router.message(Form.solving_tasks)
async def process_answer_task(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    exam_type = data["exam_type"]

    answer = message.text
    answers = data.get("answers", []) + [answer]

    task_idx = data["task_idx"] + 1
    variant_idx = data["variant_idx"]
    await state.update_data(answers=answers, task_idx=task_idx)

    max_tasks = len(listdir(join(".", exam_type, str(variant_idx)))) - (exam_type == "oge")

    if task_idx == max_tasks:
        await show_results(message, state)
        await state.set_state(None)
        await state.update_data(
            answers=[],
            task_idx=None,
            variant_idx=None
        )
    else:
        await message.delete()
        await show_task(message, state)


@form_router.message()
async def process_unknown_command(message: Message):
    await message.answer("Неизвестная команда. Введите /solve чтобы начать решение варианта.")


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands(commands=BOT_COMMANDS)

    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout)
    asyncio.run(main())
