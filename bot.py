import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ===================== CONFIG =====================
BOT_TOKEN = "8540209675:AAE67zygIFoymAZq4D8bpT9z5RgttxnbC9o"
GROUP_ID = -4701543857  # guruh ID (minus bilan!)
# ==================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ======== 12 viloyat + Toshkent shahar ========
REGIONS = [
    "Andijon", "Buxoro", "Farg‘ona", "Jizzax", "Xorazm",
    "Namangan", "Navoiy", "Qashqadaryo", "Samarqand",
    "Sirdaryo", "Surxondaryo", "Toshkent viloyati",
    "Toshkent shahri"
]

def regions_keyboard():
    rows = []
    row = []
    for r in REGIONS:
        row.append(KeyboardButton(text=r))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text="🔄 Qaytadan boshlash")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Ma’lumot yuborish")],
        ],
        resize_keyboard=True
    )

class Form(StatesGroup):
    fullname = State()
    phone = State()
    region = State()
    comment = State()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "📝 Ma’lumot yuborish uchun pastdagi tugmani bosing.",
        reply_markup=start_keyboard()
    )

@dp.message(lambda m: m.text == "🔄 Qaytadan boshlash")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔄 Qaytadan boshlandi.\n\n📝 Ma’lumot yuborish tugmasini bosing.",
        reply_markup=start_keyboard()
    )

@dp.message(lambda m: m.text == "📝 Ma’lumot yuborish")
async def begin_form(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.fullname)
    await message.answer("1) Ism familiyangizni yozing:", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Form.fullname)
async def get_fullname(message: types.Message, state: FSMContext):
    text = (message.text or "").strip()
    if len(text) < 3:
        return await message.answer("❌ Ism familiya juda qisqa. Qayta yozing:")
    await state.update_data(fullname=text)
    await state.set_state(Form.phone)
    await message.answer("2) Telefon raqam (masalan: +998901234567):")

@dp.message(Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = (message.text or "").strip().replace(" ", "")
    # oddiy tekshiruv
    if not (phone.startswith("+998") and len(phone) in (13, 14)):
        return await message.answer("❌ Telefon formati noto‘g‘ri.\nMasalan: +998901234567\nQayta kiriting:")
    await state.update_data(phone=phone)
    await state.set_state(Form.region)
    await message.answer("3) Viloyatingizni tanlang:", reply_markup=regions_keyboard())

@dp.message(Form.region)
async def get_region(message: types.Message, state: FSMContext):
    region = (message.text or "").strip()

    if region == "🔄 Qaytadan boshlash":
        await state.clear()
        return await message.answer(
            "🔄 Qaytadan boshlandi.\n📝 Ma’lumot yuborish tugmasini bosing.",
            reply_markup=start_keyboard()
        )

    if region not in REGIONS:
        return await message.answer("❌ Ro‘yxatdan tanlang:", reply_markup=regions_keyboard())

    await state.update_data(region=region)
    await state.set_state(Form.comment)
    await message.answer("4) Qo‘shimcha izoh (agar yo‘q bo‘lsa: '-' yozing):", reply_markup=types.ReplyKeyboardRemove())

@dp.message(Form.comment)
async def finish_form(message: types.Message, state: FSMContext):
    comment = (message.text or "").strip()
    if not comment:
        comment = "-"

    data = await state.get_data()
    fullname = data.get("fullname", "-")
    phone = data.get("phone", "-")
    region = data.get("region", "-")

    text_to_group = (
        "📌 Yangi ma’lumot keldi\n\n"
        f"👤 Ism: {fullname}\n"
        f"📞 Telefon: {phone}\n"
        f"🗺 Viloyat: {region}\n"
        f"📝 Izoh: {comment}\n"
    )

    try:
        await bot.send_message(GROUP_ID, text_to_group)
        await message.answer("✅ Ma’lumot yuborildi!", reply_markup=start_keyboard())
    except Exception as e:
        await message.answer(f"❌ Guruhga yuborishda xatolik: {e}\n\nToken/ID yoki bot guruhda admin emas bo‘lishi mumkin.")

    # avtomatik startga qaytadi
    await state.clear()
    await message.answer("Yana ma’lumot yuborasizmi?", reply_markup=start_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

