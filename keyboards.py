from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton

def main_menu(is_admin=False, lang='am'):
    kb = [
        [KeyboardButton(text="🎫 ቲክት ግዢ" if lang=='am' else "🎫 Buy Ticket"), KeyboardButton(text="🎟 የእኔ ቲኬቶች" if lang=='am' else "🎟 My Tickets")],
        [KeyboardButton(text="💳 የክፍያ መረጃ & ሒሳብ" if lang=='am' else "💳 Payment & Balance"), KeyboardButton(text="🏆 የአሸናፊዎች ዝርዝር" if lang=='am' else "🏆 Winners")],
        [KeyboardButton(text="👥 የግብዣ ሊንክ" if lang=='am' else "👥 Referral"), KeyboardButton(text="🌐 ቋንቋ / Language")],
        [KeyboardButton(text="📞 ድጋፍ" if lang=='am' else "📞 Support"), KeyboardButton(text="ℹ️ ስለ ሎተሪው" if lang=='am' else "ℹ️ About")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="👑 Admin Dashboard")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="አማርኛ 🇪🇹", callback_data="lang_am"), InlineKeyboardButton(text="Affan Oromoo 🇪🇹", callback_data="lang_om")],
        [InlineKeyboardButton(text="Afar Af 🇪🇹", callback_data="lang_af"), InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")]
    ])

def age_verification_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ አዎ፣ 18 ዓመት ሞልቶኛል", callback_data="age_yes")],
        [InlineKeyboardButton(text="❌ አልሞላሁም", callback_data="age_no")]
    ])

def ticket_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 ሙሉ ዕጣ - 100 ብር (100% ሽልማት)", callback_data="buy_full")],
        [InlineKeyboardButton(text="🟡 ግማሽ ዕጣ - 50 ብር (50% ሽልማት)", callback_data="buy_half")],
        [InlineKeyboardButton(text="🔙 ወደ ዋናው ሜኑ", callback_data="back_home")]
    ])

def payment_methods_keyboard(ticket_num):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 CBE (1000087841457)", callback_data=f"pay_cbe_{ticket_num}")],
        [InlineKeyboardButton(text="📱 Telebirr (0919397995)", callback_data=f"pay_tele_{ticket_num}")],
        [InlineKeyboardButton(text="📱 M-Pesa (0716357344)", callback_data=f"pay_mpesa_{ticket_num}")],
        [InlineKeyboardButton(text="💳 Chapa (Online)", callback_data=f"pay_chapa_{ticket_num}")],
        [InlineKeyboardButton(text="🔙 ሰርዝ", callback_data="back_home")]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 ስታቲስቲክስ", callback_data="adm_stats"), InlineKeyboardButton(text="💰 የክፍያ ማጽደቂያ", callback_data="adm_payments")],
        [InlineKeyboardButton(text="🎲 ዕጣ ማውጣት (Live)", callback_data="adm_draw"), InlineKeyboardButton(text="📢 ማስታወቂያ", callback_data="adm_broadcast")]
    ])
