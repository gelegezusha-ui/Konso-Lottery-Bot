import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ከሬፖዚቶሪው ውስጥ ቶከንን ማንበብ
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

# የእርስዎ የአድሚን ቴሌግራም ቻት ID
ADMIN_CHAT_ID = "1362677376"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    web_app_btn = InlineKeyboardButton("🎫 የኮንሶ ሎተሪ አፕ ይክፈቱ", url="https://gelegezusha-ui.github.io/Konso-Lottery-Bot/")
    markup.add(web_app_btn)
    
    bot.reply_to(message, 
                 "ሰላም! እንኳን ወደ **የኮንሶ ሎተሪ ቦት** በደህና መጡ።\n\nቲኬት ለመግዛት እና ዕድልዎን ለመሞከር ከታች ያለውን ሊንክ ይጫኑ!", 
                 reply_markup=markup, parse_mode="Markdown")

# ተጠቃሚው የክፍያ ስክሪንሾት ሲልክ (ስም እና ስልክ ቁጥርን ጨምሮ)
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # የላከውን መግለጫ (Caption) ማንበብ (በአፑ በኩል የተጻፈው ስም እና ስልክ እዚህ ይመጣል)
    user_caption = message.caption if message.caption else "መረጃ አልተጻፈም"
    
    # ማሳወቂያውን ለራስዎ (ለአድሚን) መላክ
    caption_text = (f"🔔 **አዲስ የክፍያ እና የቲኬት ጥያቄ መጥቷል!**\n\n"
                    f"👤 የቴሌግራም ስም: {user_name}\n"
                    f"🆔 ዩዘር ID: {user_id}\n\n"
                    f"📋 **የተጠቃሚው መረጃ እና የትዕዛዝ ዝርዝር:**\n{user_caption}\n\n"
                    f"እባክዎን ክፍያውን በባንክ/በቴሌብር አረጋግጠው ከታች ያሉትን ቁልፎች ይጫኑ።")
    
    # ለአድሚን ማጽደቂያ አዝራሮች (Approve / Reject)
    admin_markup = InlineKeyboardMarkup()
    approve_btn = InlineKeyboardButton("✅ አጽድቅ (ቲኬት ስጥ)", callback_data=f"approve_{user_id}")
    reject_btn = InlineKeyboardButton("❌ አጣጥል", callback_data=f"reject_{user_id}")
    admin_markup.add(approve_btn, reject_btn)
    
    try:
        bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=message.photo[-1].file_id, caption=caption_text, reply_markup=admin_markup, parse_mode="Markdown")
        bot.reply_to(message, "✅ የክፍያ ማረጋገጫዎ እና መረጃዎ ደርሷል! አድሚኑ ሲያረጋግጠው መልእክት ይደርሶዎታል።")
    except Exception as e:
        bot.reply_to(message, "⚠️ ስህተት አጋጥሟል። እባክዎ እንደገና ይሞክሩ።")

# አድሚኑ ቁልፍ ሲጫን የሚሰጥ ምላሽ
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    if data.startswith("approve_"):
        target_user_id = data.split("_")[1]
        bot.send_message(chat_id=target_user_id, text="🎉 እንኳን ደስ አለዎት! ክፍያዎ እና ቲኬትዎ በአድሚን ጸድቋል። መልካም ዕድል!")
        bot.answer_callback_query(call.id, "ቲኬቱ ጸድቆ ለተጠቃሚው ተልኳል!")
        bot.edit_message_caption(caption=call.message.caption + "\n\n🟢 **[ተረጋግጧል - ጸድቋል]**", reply_markup=None, chat_id=call.message.chat.id, message_id=call.message.message_id)
        
    elif data.startswith("reject_"):
        target_user_id = data.split("_")[1]
        bot.send_message(chat_id=target_user_id, text="❌ ይቅርታ፣ የላኩት የክፍያ ማረጋገጫ ወይም መረጃ ትክክለኛ አይደለም። እባክዎ አድሚኑን ያግኙ።")
        bot.answer_callback_query(call.id, "ጥያቄው ውድቅ ተደርጓል!")
        bot.edit_message_caption(caption=call.message.caption + "\n\n🔴 **[ውድቅ ተደርጓል]**", reply_markup=None, chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
