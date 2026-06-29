    import logging
from aiogram import Bot, Dispatcher, executor, types

# Direct configuration
BOT_TOKEN = "8924995974:AAEcOT5ChY4qlEl-1hguZJ_8nNFygqUOuZQ"
ADMIN_ID = 5582627293

# Logging setup
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Memory to track and filter duplicate messages
seen_messages = set()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_name = message.from_user.full_name
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["ℹ️ Profile", "⚙️ Help & Support"]
    keyboard.add(*buttons)
    
    # Show Admin Panel only to admin
    if message.from_user.id == ADMIN_ID:
        keyboard.add("👑 Admin Panel")

    await message.reply(
        f"Hello {user_name}!\nWelcome to the bot. Select an option below:",
        reply_markup=keyboard
    )

@dp.message_handler(lambda message: message.text and not message.text.startswith('/'))
async def filter_and_reply(message: types.Message):
    text = message.text.strip()
    
    # Admin section
    if text == "👑 Admin Panel" and message.from_user.id == ADMIN_ID:
        await message.answer("👑 Welcome Admin! Duplicate filter system is active.")
        return

    # Menu handlers
    if text == "ℹ️ Profile":
        await message.answer(f"👤 Name: {message.from_user.full_name}\n🆔 ID: {message.from_user.id}")
        return
    elif text == "⚙️ Help & Support":
        await message.answer("Please contact the admin for any support.")
        return

    # Duplicate filter system
    if text in seen_messages:
        logging.info(f"Ignored duplicate message: {text}")
        return
    
    # Save message to memory
    seen_messages.add(text)
    
    # Keep memory clean (limit to last 100 messages)
    if len(seen_messages) > 100:
        seen_messages.pop()

    await message.answer(f"Request received: {text}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
                                        
