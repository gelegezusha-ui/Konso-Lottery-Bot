import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from keyboards import get_main_menu

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    init_db()
    is_admin = (message.from_user.id == ADMIN_ID)
    await message.answer(
        f"ሰላም <b>{message.from_user.full_name}</b>!\nእንኳን ወደ <b>Konso Lottery Bot</b> በደህና መጡ።",
        reply_markup=get_main_menu(is_admin),
        parse_mode="HTML"
    )

@dp.message(F.text == "ℹ️ ስለ ሎተሪው")
async def about_lottery(message: Message):
    text = (
        "🎫 <b>Konso Lottery መግለጫ</b>\n\n"
        "ቁጥሮች ከ 001 እስከ 1000 አሉ።\n"
        "🟢 ሙሉ ዕጣ: 500 ብር (ሙሉ ሽልማት)\n"
        "🟡 ግማሽ ዕጣ: 250 ብር (50% ሽልማት)\n\n"
        "🏆 <b>ዋና ዋና ሽልማቶች:</b>\n"
        "1ኛ: 400,000 ብር\n"
        "2ኛ: 10,000 ብር\n"
        "3ኛ: 5,000 ብር\n"
        "4ኛ: 2,500 ብር\n"
        "5ኛ: 1,000 ብር\n"
        "6ኛ: 500 ብር"
    )
    await message.answer(text, parse_mode="HTML")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
