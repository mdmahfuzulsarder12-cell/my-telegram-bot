import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 1. Configuration
API_TOKEN = '8924995974:AAEcOT5ChY4qlEl-1hguZJ_8nNFygqUOuZQ'
ADMIN_ID = 5582627293  
CHANNEL_USERNAME = '@A_ToolsX'  

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize Bot and Dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Local memory to prevent checking the channel repeatedly
verified_users = set()

# Function to check channel membership
async def check_channel_join(user_id):
    if user_id in verified_users:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            verified_users.add(user_id)  # Save to memory so it doesn't check again
            return True
        return False
    except Exception:
        return False

# Inline keyboard for joining the channel
def get_join_keyboard():
    keyboard = InlineKeyboardMarkup()
    btn_link = InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
    btn_check = InlineKeyboardButton("🔄 Check Join", callback_data="check_join")
    keyboard.add(btn_link)
    keyboard.add(btn_check)
    return keyboard

# Reply menu keyboard
def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("Register", "My account")
    keyboard.row("Balance", "Help")
    keyboard.row("Referral Program")
    return keyboard

# Start command handler
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_channel_join(user_id):
        await message.answer(
            f"🚀 To use this bot, you must join our channel: {CHANNEL_USERNAME}",
            reply_markup=get_join_keyboard()
        )
        return

    await message.answer("Welcome back! Choose an option from the menu.", reply_markup=get_main_menu())

# Callback query handler for checking join status
@dp.callback_query_handler(text="check_join")
async def process_check_join(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if await check_channel_join(user_id):
        await bot.answer_callback_query(callback_query.id, "Thank you for joining!")
        await bot.send_message(user_id, "Access granted! Welcome to the bot.", reply_markup=get_main_menu())
    else:
        await bot.answer_callback_query(callback_query.id, "You haven't joined yet!", show_alert=True)

# Main menu buttons handler
@dp.message_handler(lambda message: message.text in ["Register", "My account", "Balance", "Help", "Referral Program"])
async def handle_menu(message: types.Message):
    user_id = message.from_user.id
    
    if not await check_channel_join(user_id):
        await message.answer("Please join our channel first!", reply_markup=get_join_keyboard())
        return

    text = message.text
    if text == "Register":
        await message.answer("Registration process started...")
    elif text == "My account":
        await message.answer(f"👤 Your Account\nID: {user_id}")
    elif text == "Balance":
        await message.answer("💰 Your current balance is: 0.00")
    elif text == "Help":
        await message.answer("ℹ️ Contact Support if you face any issues.")
    elif text == "Referral Program":
        await message.answer("🔗 Invite friends and earn benefits!")

# Admin panel logic
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Welcome Boss! This is your secret admin panel.")
    else:
        await message.answer("Unauthorized access.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
        
