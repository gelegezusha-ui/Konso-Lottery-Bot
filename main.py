import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN, ADMIN_ID
from database import init_db, get_db
from keyboards import main_menu, language_keyboard, age_verification_keyboard, ticket_type_keyboard, payment_methods_keyboard, admin_keyboard

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    waiting_for_proof = State()
    waiting_for_broadcast = State()

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, age_verified, language FROM users WHERE telegram_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        referred_by = None
        if len(args) > 1 and args[1].isdigit():
            ref_id = int(args[1])
            if ref_id != user_id:
                cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (ref_id,))
                if cursor.fetchone():
                    referred_by = ref_id
                    # Give 25 ETB bonus to referrer
                    cursor.execute("UPDATE users SET balance = balance + 25 WHERE telegram_id = ?", (ref_id,))
                    
        cursor.execute("INSERT INTO users (telegram_id, name, referred_by) VALUES (?, ?, ?)", 
                       (user_id, message.from_user.full_name, referred_by))
        conn.commit()
        cursor.execute("SELECT id, age_verified, language FROM users WHERE telegram_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    
    # Send promotional poster if available
    try:
        photo = FSInputFile("file_000000004c8c81f49c6517c715e45acf.png")
        await message.answer_photo(photo, caption="✨ **ፋል አው! ቲክት ግዢ፣ እዳል ወስደው!**\nቁጥሮች ከ 001 እስከ 1000 አሉ።")
    except:
        pass

    if not user[1]: # age_verified == 0
        await message.answer("⚠️ እባክዎ ዕድሜዎ ከ **18 ዓመት በላይ** መሆኑን ያረጋግጡ:", reply_markup=age_verification_keyboard())
    else:
        is_admin = (user_id == ADMIN_ID)
        await message.answer("እንኳን ወደ **Konso Lottery (ROUND #05)** በደህና መጡ! የሚፈልጉትን አማራጭ ይምረጡ:", reply_markup=main_menu(is_admin, user[2]))

@dp.callback_query(F.data.startswith("age_"))
async def process_age(callback: CallbackQuery):
    user_id = callback.from_user.id
    if callback.data == "age_no":
        await callback.message.answer("⚠️ ዕድሜዎ ከ 18 ዓመት በታች ስለሆነ ቦቱን መጠቀም አይችሉም።")
        await callback.answer()
        return
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET age_verified = 1 WHERE telegram_id = ?", (user_id,))
    conn.commit()
    cursor.execute("SELECT language FROM users WHERE telegram_id = ?", (user_id,))
    lang = cursor.fetchone()[0]
    conn.close()
    
    is_admin = (user_id == ADMIN_ID)
    await callback.message.answer("✅ እናመሰግናለን! አሁን ወደ ዋናው ገጽ ገብተዋል።", reply_markup=main_menu(is_admin, lang))
    await callback.answer()

@dp.message(F.text == "🌐 ቋንቋ / Language")
async def choose_language(message: Message):
    await message.answer("እባክዎ የሚፈልጉትን ቋንቋ ይምረጡ / Please choose your language:", reply_markup=language_keyboard())

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (lang, callback.from_user.id))
    conn.commit()
    conn.close()
    await callback.message.answer("✅ ቋንቋዎ ተቀይሯል!")
    is_admin = (callback.from_user.id == ADMIN_ID)
    await callback.message.answer("ዋናው ሜኑ:", reply_markup=main_menu(is_admin, lang))
    await callback.answer()

@dp.message(F.text.in_(["🎫 ቲክት ግዢ", "🎫 Buy Ticket"]))
async def ticket_menu(message: Message):
    text = (
        "🎫 **ROUND #05 - ቲክት ግዢ**\n\n"
        "• 🟢 ሙሉ ዕጣ: 100 ብር (ሙሉ ሽልማት 400,000 ብር)\n"
        "• 🟡 ግማሽ ዕጣ: 50 ብር (50% ሽልማት 200,000 ብር)\n\n"
        "አንድ ቁጥር ከአንድ ሰው በላይ አይሸጥም! ከታች ይምረጡ:"
    )
    await message.answer(text, reply_markup=ticket_type_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def select_ticket_type(callback: CallbackQuery):
    t_type = "full" if callback.data == "buy_full" else "half"
    price = 100 if t_type == "full" else 50
    
    conn = get_db()
    cursor = conn.cursor()
    # Find available ticket
    cursor.execute("SELECT number FROM tickets WHERE status = 'available' AND round = 5 LIMIT 1")
    ticket = cursor.fetchone()
    
    if not ticket:
        await callback.message.answer("ይቅርታ! ሁሉም 1000 ቲኬቶች ተሸጠዋል።")
        await callback.answer()
        return
        
    num = ticket[0]
    conn.close()
    
    text = f"🎫 የተሰጠዎት ቲኬት ቁጥር: **{num}**\nዋጋ: **{price} ብር**\n\nክፍያ የሚፈጽሙበትን ባንክ ይምረጡ:"
    await callback.message.answer(text, reply_markup=payment_methods_keyboard(num), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    method = parts[1]
    ticket_num = parts[2]
    
    await state.update_data(ticket_num=ticket_num, method=method)
    await callback.message.answer(
        f"💳 የተመረጠው ባንክ: **{method.upper()}**\n"
        f"ቲኬት ቁጥር: **{ticket_num}**\n\n"
        "እባክዎ ክፍያውን ከፈጸሙ በኋላ **የክፍያ ማረጃውን (Screenshot)** እዚህ ይላኩላቸው።"
    )
    await state.set_state(Form.waiting_for_proof)
    await callback.answer()

@dp.message(Form.waiting_for_proof, F.photo)
async def receive_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    ticket_num = data.get("ticket_num")
    method = data.get("method")
    photo_id = message.photo[-1].file_id
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET status = 'pending', owner_id = ? WHERE number = ?", (message.from_user.id, ticket_num))
    cursor.execute("INSERT INTO payments (user_id, amount, method, proof, status) VALUES (?, 100, ?, ?, 'pending')",
                   (message.from_user.id, method, photo_id))
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer("⏳ የክፍያ ማረጃዎ ደርሷል! አድሚኑ እስኪያረጋግጠው በpending ላይ ይገኛል።")
    
    # Notify Admin with inline buttons to approve/reject
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"apv_{payment_id}_{ticket_num}"),
         InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"rej_{payment_id}_{ticket_num}")]
    ])
    await bot.send_photo(ADMIN_ID, photo=photo_id, caption=f"🔔 አዲስ ክፍያ ማረጃ!\nተጠቃሚ ID: {message.from_user.id}\nቲኬት: {ticket_num}\nባንክ: {method}", reply_markup=admin_kb)

@dp.callback_query(F.data.startswith(("apv_", "rej_")))
async def admin_verify_payment(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("ፈቃድ የለዎትም!", show_alert=True)
        return
        
    action, pay_id, ticket_num = callback.data.split("_")
    conn = get_db()
    cursor = conn.cursor()
    
    if action == "apv":
        cursor.execute("UPDATE payments SET status = 'approved' WHERE id = ?", (pay_id,))
        cursor.execute("UPDATE tickets SET status = 'sold' WHERE number = ?", (ticket_num,))
        conn.commit()
        
        # Get user_id from payments
        cursor.execute("SELECT user_id FROM payments WHERE id = ?", (pay_id,))
        uid = cursor.fetchone()[0]
        cursor.execute("SELECT telegram_id FROM users WHERE id = ?", (uid,))
        tg_id = cursor.fetchone()[0]
        
        await bot.send_message(tg_id, f"🎉 እንኳን ደስ አለዎት! የቲኬት ቁጥር **{ticket_num}** ክፍያዎ **ጸድቋል** (Sold)! ቁጥርዎ አረንጓዴ ሆኗል።")
        await callback.message.edit_caption(caption=f"✅ ክፍያው ጸድቋል (Approved) - ቲኬት: {ticket_num}")
    else:
        cursor.execute("UPDATE payments SET status = 'rejected' WHERE id = ?", (pay_id,))
        cursor.execute("UPDATE tickets SET status = 'available', owner_id = NULL WHERE number = ?", (ticket_num,))
        conn.commit()
        
        cursor.execute("SELECT user_id FROM payments WHERE id = ?", (pay_id,))
        uid = cursor.fetchone()[0]
        cursor.execute("SELECT telegram_id FROM users WHERE id = ?", (uid,))
        tg_id = cursor.fetchone()[0]
        
        await bot.send_message(tg_id, f"❌ ይቅርታ፣ የቲኬት ቁጥር **{ticket_num}** ክፍያዎ **ውድቅ ተደርጓል** (Rejected)። እባክዎ በትክክል እንደገና ይሞክሩ።")
        await callback.message.edit_caption(caption=f"❌ ክፍያው ውድቅ ተደርጓል (Rejected) - ቲኬት: {ticket_num}")
        
    conn.close()
    await callback.answer()

@dp.message(F.text.in_(["🎟 የእኔ ቲኬቶች", "🎟 My Tickets"]))
async def my_tickets(message: Message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user:
        await message.answer("እስካሁን ምንም ቲኬት የለዎትምም።")
        conn.close()
        return
        
    cursor.execute("SELECT number, type, status FROM tickets WHERE owner_id = ?", (user[0],))
    tickets = cursor.fetchall()
    conn.close()
    
    if not tickets:
        await message.answer("እስካሁን የገዙት ቲኬት የለም።")
        return
        
    text = "🎟 **የገዙዋቸው ቲኬቶች (🔴 የተሸጠ/የጸደቀ፣ 🟢 ክፍያ በመጠበቅ ላይ):**\n\n"
    for t in tickets:
        status_icon = "🔴" if t[2] == 'sold' else "🟡"
        text += f"{status_icon} ቲኬት ቁጥር: **{t[0]}** | ዓይነት: {t[1]}\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.in_(["💳 የክፍያ መረጃ & ሒሳብ", "💳 Payment & Balance"]))
async def payment_info(message: Message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    conn.close()
    
    text = (
        f"💳 **የሂሳብ እና የባንክ መረጃ (ROUND #05):**\n\n"
        f"💰 የእርስዎ ቀሪ ሂሳብ: **{bal} ብር**\n\n"
        f"🏦 **CBE (ኢትዮጵያ ንግድ ባንክ):** `1000087841457`\n"
        f"📱 **Telebirr:** `0919397995`\n"
        f"📱 **M-Pesa:** `0716357344`\n"
        f"💳 **Chapa Online Payment:** በቅርቡ በFully Verified አካውንት ይሰራል።\n\n"
        f"*(ለማስወጣት/Withdraw ከባለቤቱ ጋር በስልክ ያነጋግሩ)*"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.in_(["👥 የግብዣ ሊንክ", "👥 Referral"]))
async def referral_link(message: Message):
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    text = (
        f"👥 **ጓደኛዎን በመጋበዝ 25 ብር ይሸለሙ!**\n\n"
        f"ይህንን የግብዣ ሊንክ ለጓደኛዎ በመላክ ቦቱን ሲጠቀሙ የ 25 ብር ቦነስ ያግኙ፦\n`{link}`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.in_(["🏆 የአሸናፊዎች ዝርዝር", "🏆 Winners"]))
async def winners_info(message: Message):
    text = (
        "🏆 **ROUND #05 - ዋና ዋና ሽልማቶች:**\n\n"
        "🥇 1ኛ አሸናፊ: 400,000 ብር\n"
        "🥈 2ኛ አሸናፊ: 10,000 ብር\n"
        "🥉 3ኛ አሸናፊ: 5,000 ብር\n"
        "🏅 4ኛ አሸናፊ: 2,500 ብር\n"
        "🏅 5ኛ አሸናፊ: 1,000 ብር\n"
        "🏅 6ኛ አሸናፊ: 500 ብር\n\n"
        "⏳ *ዕጣው 1000 ቲኬት ሲሞላ አውቶማቲክ ከ 3 ቀን በኋላ በ Live ይወጣል!*"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.in_(["📞 ድጋፍ", "📞 Support"]))
async def support_info(message: Message):
    await message.answer("📞 **ፈጣን ድጋፍ እና እხმარታ:**\nስልክ: 0919397995 / 0716357344\nቲክቶክ: @konsolottery")

@dp.message(F.text.in_(["ℹ️ ስለ ሎተሪው", "ℹ️ About"]))
async def about_bot(message: Message):
    text = (
        "ℹ️ ይህ የኮንሶ ሎተሪ ቦት በበኢትዮጵያዊ ወጣትና ታማኝ ወንድማችሁ ገዝሃኝ የተዘጋጀ ታማኝ የዕጣ ማውጫ መድረክ ነው።\n\n"
        "ለበለጠ መረጃ:- 0919397995 / 0716357344 ይደውሉልን።"
    )
    await message.answer(text)

@dp.message(F.text == "👑 Admin Dashboard")
async def admin_dash(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("👑 **Admin Dashboard**", reply_markup=admin_keyboard())

@dp.callback_query(F.data == "admin_stats")
async def adm_stats(callback: CallbackQuery):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'sold'")
    sold = cursor.fetchone()[0]
    conn.close()
    await callback.message.answer(f"📊 የተሸጡ ቲኬቶች ብዛት: {sold} / 1000")
    await callback.answer()

@dp.callback_query(F.data == "back_home")
async def back_home(callback: CallbackQuery):
    is_admin = (callback.from_user.id == ADMIN_ID)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    res = cursor.fetchone()
    lang = res[0] if res else 'am'
    conn.close()
    await callback.message.answer("ወደ ዋናው ሜኑ ተመለሰዋል:", reply_markup=main_menu(is_admin, lang))
    await callback.answer()

async def main():
    init_db()
    print("Konso Lottery Bot is running successfully...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
