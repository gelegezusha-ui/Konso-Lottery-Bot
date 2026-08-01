from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton

def main_menu(is_admin=False):
    keyboard = [
        [KeyboardButton(text="🎫 ቲክት ግዢ"), KeyboardButton(text="🎟 የእኔ ቲኬቶች")],
        [KeyboardButton(text="💳 የክፍያ መረጃ"), KeyboardButton(text="🏆 የአሸናፊዎች ዝርዝር")],
        [KeyboardButton(text="📞 ድጋፍ"), KeyboardButton(text="ℹ️ ስለ ሎተሪው")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="👑 Admin Dashboard")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def ticket_type_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🟢 ሙሉ ዕጣ (500 ብር)", callback_data="buy_full")],
        [InlineKeyboardButton(text="🟡 ግማሽ ዕጣ (250 ብር)", callback_data="buy_half")],
        [InlineKeyboardButton(text="🔙 ወደ ዋናው ሜኑ", callback_data="back_home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def payment_methods_keyboard(ticket_num):
    keyboard = [
        [InlineKeyboardButton(text="ኢትዮጵያ ንግድ ባንክ (CBE)", callback_data=f"pay_cbe_{ticket_num}")],
        [InlineKeyboardButton(text="ቴሌብር (Telebirr)", callback_data=f"pay_tele_{ticket_num}")],
        [InlineKeyboardButton(text="አም-ፔሳ (M-Pesa)", callback_data=f"pay_mpesa_{ticket_num}")],
        [InlineKeyboardButton(text="🔙 ሰርዝ", callback_data="back_home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="📊 ስታቲስቲክስ", callback_data="admin_stats"), InlineKeyboardButton(text="👥 ተጠቃሚዎች", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 ክፍያዎች ማረጋገጫ", callback_data="admin_payments"), InlineKeyboardButton(text="🎲 ዕጣ ማስጀመር", callback_data="admin_draw")],
        [InlineKeyboardButton(text="📢 ማስታወቂያ መላክ", callback_data="admin_broadcast")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
