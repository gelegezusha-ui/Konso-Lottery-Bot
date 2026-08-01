import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN, ADMIN_ID
from database import init_db, get_db
from keyboards import main_menu, ticket_type_keyboard, payment_methods_keyboard, admin_keyboard

# Logging setup
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class PurchaseState(StatesGroup):
    choosing_ticket = State()
    waiting_for_proof = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, name) VALUES (?, ?)", 
                   (message.from_user.id, message.from_user.full_name))
    conn.commit()
    conn.close()
    
    is_admin = (message.from_user.id == ADMIN_ID)
    
    welcome_text = (
        f"ሰላም 🇪🇹 ጂኤ ህትመትና ፎቶ Editing ድርጅት GA Printing and Photo Editing!\n"
        f"እንኳን ወደ Konso Lottery Bot በደህና መጡ::"
    )
    await message.answer(welcome_text, reply_markup=main_menu(is_admin))

# --- Main Menu Handlers ---
@dp.message(F.text == "🎫 ቲክት ግዢ")
async def ticket_purchase(message: Message):
    text = (
        "🎫 **Konso Lottery ማግለጫ**\n\n"
        "ቁጥሮች ከ 001 እስከ 1000 አሉ።\n"
        "🟢 ሙሉ ዕጣ: 500 ብር (ሙሉ ሽልማት)\n"
        "🟡 ግማሽ ዕጣ: 250 ብር (50% ሽልማት)\n\n"
        "የሚፈልጉትን የዕጣ ዓይነት ይምረጡ:"
    )
    await message.answer(text, reply_markup=ticket_type_keyboard(), parse_mode="Markdown")

@dp.message(F.text == "🎟 የእኔ ቲኬቶች")
async def my_tickets(message: Message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT number, type, status FROM tickets WHERE owner_id = ?", (message.from_user.id,))
    tickets = cursor.fetchall()
    conn.close()
    
    if not tickets:
        await message.answer("እስካሁን የገዙት ቲኬት የለም።")
        return
        
    text = "🎟 **የገዙዋቸው ቲኬቶች ዝርዝር:**\n\n"
    for t in tickets:
        t_type = "ሙሉ (500 ብር)" if t[1] == 'full' else "ግማሽ (250 ብር)"
        text += f"• ቁጥር: **{t[0]}** | ዓይነት: {t_type} | ሁኔታ: {t[2]}\n"
        
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "💳 የክፍያ መረጃ")
async def payment_info(message: Message):
    info_text = (
        "💳 **የክፍያ አካውንቶች መረጃ:**\n\n"
        "🏦 **CBE (ኢትዮጵያ ንግድ ባንክ):**\n`1000087841457`\n\n"
        "📱 **Telebirr:**\n`0919397995`\n\n"
        "📱 **M-Pesa:**\n`0716357344`\n\n"
        "ክፍያ ከፈጸሙ በኋላ ደረሰኙን (Screenshot) በመላክ ማረጋገጫ ማስገባት ይችላሉ።"
    )
    await message.answer(info_text, parse_mode="Markdown")

@dp.message(F.text == "🏆 የአሸናፊዎች ዝርዝር")
async def winners_list(message: Message):
    text = (
        "🏆 **ዋና ዋና ሽልማቶች:**\n\n"
        "🥇 1ኛ አሸናፊ: 400,000 ብር\n"
        "🥈 2ኛ አሸናፊ: 10,000 ብር\n"
        "🥉 3ኛ አሸናፊ: 5,000 ብር\n"
        "🏅 4ኛ አሸናፊ: 2,500 ብር\n"
        "🏅 5ኛ አሸናፊ: 1,000 ብር\n"
        "🏅 6ኛ አሸናፊ: 500 ብር\n\n"
        "ዕጣው 1000 ቲኬት ሲሞላ በድምቀት ይወጣል!"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📞 ድጋፍ")
async def support_info(message: Message):
    await message.answer("📞 ለምታስፈልጉት እხმარታ በባለቤቱ ስልክ ቁጥር 0919397995 ወይም በድርጅቱ በኩል ማግኘት ይችላሉ።")

@dp.message(F.text == "ℹ️ ስለ ሎተሪው")
async def about_lottery(message: Message):
    await message.answer("ℹ️ ይህ የኮንሶ ሎተሪ ቦት በ GA Printing and Photo Editing የተዘጋጀ ታማኝ የዕጣ ማውጫ መድረክ ነው።")

@dp.message(F.text == "👑 Admin Dashboard")
async def admin_dashboard(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("ይህንን ትዕዛዝ ለመጠቀም ፈቃድ አለዎት።")
        return
    await message.answer("👑 **የአስተዳዳሪ መቆጣጠሪያ ፓነል (Admin Dashboard)**", reply_markup=admin_keyboard(), parse_mode="Markdown")

# --- Inline Callback Handling for Ticket Purchase ---
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_type(callback: CallbackQuery):
    t_type = "full" if callback.data == "buy_full" else "half"
    
    # Find first available ticket
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT number FROM tickets WHERE status = 'available' AND round = 1 LIMIT 1")
    ticket = cursor.fetchone()
    
    if not ticket:
        await callback.message.answer("ይቅርታ! ሁሉም ቲኬቶች ተሸጠዋል።")
        await callback.answer()
        return
        
    num = ticket[0]
    conn.close()
    
    price = "500 ብር" if t_type == "full" else "250 ብር"
    text = f"🎫 የተመረጠው ቲኬት ቁጥር: **{num}**\nየዕጣ ዓይነት: {price}\n\nእಯم ክፍያ የሚፈጽሙበትን ባንክ ይምረጡ:"
    await callback.message.answer(text, reply_markup=payment_methods_keyboard(num), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    method = data_parts[1]
    ticket_num = data_parts[2]
    
    await state.update_data(ticket_num=ticket_num, method=method)
    await callback.message.answer(f"እባክዎ የመረጡትን የክፍያ ማረጃ (Screenshot) አሁን ይላኩላቸው።")
    await state.set_state(PurchaseState.waiting_for_proof)
    await callback.answer()

@dp.message(PurchaseState.waiting_for_proof, F.photo)
async def receive_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_num = data.get("ticket_num")
    method = data.get("method")
    
    photo_id = message.photo[-1].file_id
    
    conn = get_db()
    cursor = conn.cursor()
    # Mark ticket as pending
    cursor.execute("UPDATE tickets SET status = 'pending', owner_id = ? WHERE number = ?", (message.from_user.id, ticket_num))
    cursor.execute("INSERT INTO payments (user_id, amount, method, proof, status) VALUES (?, ?, ?, ?, 'pending')",
                   (message.from_user.id, 500 if method=='full' else 250, method, photo_id))
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer("✅ የክፍያ ማረጃዎ ደርሷል! አድሚኑ ሲያረጋግጠው ቲኬቱ ይጸድቃል።")
    
    # Notify Admin
    await bot.send_message(ADMIN_ID, f"🔔 አዲስ የክፍያ ማረጃ መጥቷል!\nተጠቃሚ ID: {message.from_user.id}\nቲኬት ቁጥር: {ticket_num}")

@dp.callback_query(F.data == "back_home")
async def back_home(callback: CallbackQuery):
    is_admin = (callback.from_user.id == ADMIN_ID)
    await callback.message.answer("ወደ ዋናው ሜኑ ተመለሰዋል:", reply_markup=main_menu(is_admin))
    await callback.answer()

# --- Admin Callback Actions ---
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status != 'available'")
    sold = cursor.fetchone()[0]
    conn.close()
    
    await callback.message.answer(f"📊 **የስታቲስቲክስ መረጃ:**\n\nተሸጡ ቲኬቶች ብዛት: {sold} / 1000", parse_mode="Markdown")
    await callback.answer()

async def main():
    init_db()
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
