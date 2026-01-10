import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ================== SOZLAMALAR ==================
TOKEN = "8540209675:AAE67zygIFoymAZq4D8bpT9z5RgttxnbC9o"
GROUP_ID = -4701543857  # ishlamasa: -1004701543857 qilib ko'ring
# =================================================

logging.basicConfig(level=logging.INFO)


class Order(StatesGroup):
    number = State()
    phone = State()
    region = State()
    amount = State()
    name = State()


REGIONS = [
    "Toshkent", "Farg‘ona", "Sirdaryo", "Surxondaryo",
    "Samarqand", "Buxoro", "Andijon", "Namangan",
    "Xorazm", "Qoraqalpog‘iston", "Jizzax", "Qashqadaryo", "Navoiy"
]

REGIONS_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=r)] for r in REGIONS],
    resize_keyboard=True
)


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(CommandStart())
    async def start(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("📦 Buyurtma raqamini kiriting:")
        await state.set_state(Order.number)

    @dp.message(Order.number)
    async def step_number(message: Message, state: FSMContext):
        await state.update_data(number=message.text.strip())
        await message.answer("📞 Telefon raqamni kiriting:")
        await state.set_state(Order.phone)

    @dp.message(Order.phone)
    async def step_phone(message: Message, state: FSMContext):
        await state.update_data(phone=message.text.strip())
        await message.answer("📍 Viloyatni tanlang:", reply_markup=REGIONS_KB)
        await state.set_state(Order.region)

    @dp.message(Order.region)
    async def step_region(message: Message, state: FSMContext):
        await state.update_data(region=message.text.strip())
        await message.answer("💰 Summani kiriting (faqat raqam):", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Order.amount)

    @dp.message(Order.amount)
    async def step_amount(message: Message, state: FSMContext):
        raw = message.text.strip().replace(" ", "")
        if not raw.isdigit():
            await message.answer("❌ Faqat raqam kiriting. Masalan: 1450000")
            return
        amount = "{:,}".format(int(raw)).replace(",", " ")
        await state.update_data(amount=amount)
        await message.answer("👤 Mutaxasis ismini kiriting:")
        await state.set_state(Order.name)

    @dp.message(Order.name)
    async def finish(message: Message, state: FSMContext):
        data = await state.get_data()
        name = message.text.strip()

        # ✅ Bitta qator xabar
        text = (
            f"{data['number']} - {data['phone']} - {data['region']} - "
            f"{data['amount']} so‘m - {name} | Tavsiya bering"
        )

        await bot.send_message(GROUP_ID, text)

        # ✅ Avtomatik qayta start
        await state.clear()
        await message.answer("✅ Yuborildi. 📦 Yangi buyurtma raqamini kiriting:")
        await state.set_state(Order.number)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

