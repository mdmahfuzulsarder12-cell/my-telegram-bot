import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = "8924995974:AAEKVpB992nDx3oVhvIbwD4601F-ZHHqQJA"
ADMIN_ID = 5582627293
AUTO_APPROVE = True

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, hold REAL DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, email TEXT, status TEXT)")
conn.commit()

class Form(StatesGroup):
    email = State()
    address = State()
    amount = State()

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (msg.from_user.id,))
    conn.commit()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Register", "My Account")
    kb.add("Balance", "Help")

    await msg.answer("Welcome 🚀", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Back", state="*")
async def back(msg: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await start(msg)

@dp.message_handler(lambda m: m.text == "Register")
async def register(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Submit Account", "Back")
    await msg.answer("Choose option", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Submit Account")
async def submit(msg: types.Message):
    await msg.answer("Enter Email:")
    await Form.email.set()

@dp.message_handler(state=Form.email)
async def get_email(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    status = "Approved" if AUTO_APPROVE else "Pending"

    cursor.execute(
        "INSERT INTO accounts (user_id, email, status) VALUES (?, ?, ?)",
        (user_id, msg.text, status)
    )

    if status == "Approved":
        cursor.execute("UPDATE users SET hold = hold + 0.17 WHERE user_id=?", (user_id,))

    conn.commit()

    await msg.answer(f"Submitted ✅\nStatus: {status}")
    await state.finish()
    await start(msg)

@dp.message_handler(lambda m: m.text == "Balance")
async def balance(msg: types.Message):
    cursor.execute("SELECT balance, hold FROM users WHERE user_id=?", (msg.from_user.id,))
    data = cursor.fetchone()

    if data:
        b, h = data
    else:
        b, h = 0, 0

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Payout", "Back")

    await msg.answer(f"Balance: {b}\nHold: {h}", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Payout")
async def payout(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("LTC", "Back")
    await msg.answer("Select method", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "LTC")
async def ltc(msg: types.Message):
    await msg.answer("Enter LTC Address:")
    await Form.address.set()

@dp.message_handler(state=Form.address)
async def get_address(msg: types.Message, state: FSMContext):
    await state.update_data(address=msg.text)
    await msg.answer("Enter amount ($5 min):")
    await Form.amount.set()

@dp.message_handler(state=Form.amount)
async def get_amount(msg: types.Message, state: FSMContext):
    try:
        amt = float(msg.text)
    except ValueError:
        await msg.answer("Invalid amount. Please enter a valid number.")
        return

    cursor.execute("SELECT balance FROM users WHERE user_id=?", (msg.from_user.id,))
    res = cursor.fetchone()
    
    bal = res[0] if res else 0

    if amt < 5:
        await msg.answer("Minimum $5")
    elif amt > bal:
        await msg.answer("Not enough balance")
    else:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amt, msg.from_user.id))
        conn.commit()
        await msg.answer("Withdraw request sent ✅")
        await state.finish()
        await start(msg)
        return

    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
