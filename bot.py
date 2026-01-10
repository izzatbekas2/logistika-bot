import os
import re
import logging
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
GROUP_ID_RAW = os.environ.get("GROUP_ID")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN env variable is missing (Railway Settings -> Variables)")
if not GROUP_ID_RAW:
    raise RuntimeError("GROUP_ID env variable is missing (Railway Settings -> Variables)")

GROUP_ID = int(GROUP_ID_RAW)

REGIONS = [
    "Toshkent shahri", "Toshkent", "Andijon", "Buxoro", "Farg‘ona", "Jizzax",
    "Namangan", "Navoiy", "Qashqadaryo", "Samarqand", "Sirdaryo", "Surxondaryo",
    "Xorazm", "Qoraqalpog‘iston",
]

class Form(StatesGroup):
    order_no = State()
    phone = State()
    region = State()
    amount = State()
    name = State()

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def region_keyboard() -> types.ReplyKeyboardMarkup:
    rows, row = [], []
    for i, r in enumerate(REGIONS, start=1):
        row.append(types.KeyboardButton(text=r))
        if i % 2 == 0:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return types.ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def clean_phone(text: str) -> str:
    digits = re.sub(r"\D", "", text)
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 9:
        return f"+998{digits}"
    return text.strip()

def clean_amount(text: str) -> str:
    digits = re.sub(r"\D", "", text)
    return digits if digits else text.strip()

@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("1) Buyurtma raqamini kiriting (masalan: 74):")
    await state.set_state(Form.order_no)

@dp.message(Form.order_no)
async def step_order(message: types.Message, state: FSMContext):
    await state.update_data(order_no=message.text.strip())
    await message.answer("2) Telefon raqamini kiriting (masalan: +998901234567):")
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def step_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=clean_phone(message.text))
    await message.answer("3) Viloyatni tanlang:", reply_markup=region_keyboard())
    await state.set_state(Form.region)

@dp.message(Form.region)
async def step_region(message: types.Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS:
        await message.answer("Tugmadan tanlang 👇", reply_markup=region_keyboard())
        return
    await state.update_data(region=region)
    await message.answer("4) Summani kiriting (masalan: 650000):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Form.amount)

@dp.message(Form.amount)
async def step_amount(message: types.Message, state: FSMContext):
    await state.update_data(amount=clean_amount(message.text))
    await message.answer("5) Mutaxasis ismini kiriting (masalan: abdulloh):")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def step_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    data = await state.get_data()
    order_no = data.get("order_no", "")
    phone = data.get("phone", "")
    region = data.get("region", "")
    amount = data.get("amount", "")

    msg = f"{order_no} - {phone} {region.lower()} yetkazildi tavsiya bering {amount} {name}"
    await bot.send_message(GROUP_ID, msg)

    await message.answer("✅ Yuborildi!\nYana /start bosing.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
