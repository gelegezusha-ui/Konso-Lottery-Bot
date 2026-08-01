from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu(is_admin: bool = False):
    keyboard = [
        [KeyboardButton(text="🎫 ቲኬት ግዛ"), KeyboardButton(text="🎟 የእኔ ቲኬቶች")],
        [KeyboardButton(text="🏆 የአሸናፊዎች ዝርዝር"), KeyboardButton(text="💳 የክፍያ መረጃ")],
        [KeyboardButton(text="📞 ድጋፍ"), KeyboardButton(text="ℹ️ ስለ ሎተሪው")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="👑 Admin Dashboard")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_payment_methods():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="CBE"), KeyboardButton(text="Telebirr")],
            [KeyboardButton(text="M-Pesa"), KeyboardButton(text="Chapa")],
            [KeyboardButton(text="🔙 ተመለስ")]
        ],
        resize_keyboard=True
    )
