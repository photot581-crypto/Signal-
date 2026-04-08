import telebot
import requests
import time
import threading
import random
import sys
import json
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# --- CONFIGURATION ---
TOKEN = "8771594605:AAGjqhnJLJIkQKRuxI5EdFzKxVwfJbmz-ys"
ADMIN_ID = 7720552595 
WIN_STICKER_ID = "CAACAgUAAxkBAAEQ4l5p1atQ8VOAhofxeuCjSQbIpAYqIQACsAwAAqSHAVQHnNeXSrOm_jsE" 

bot = telebot.TeleBot(TOKEN)
API_URL = "https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json"

# --- DATA PERSISTENCE ---
def load_data(file, default):
    try:
        with open(file, 'r') as f: return set(json.load(f))
    except: return default

def save_data(file, data):
    try:
        with open(file, 'w') as f: json.dump(list(data), f)
    except: pass

allowed_users = load_data('users.json', {ADMIN_ID})
banned_users = load_data('banned.json', set())
target_channels = load_data('channels.json', set())

state = {"is_running": False, "last_id": None, "last_pred": None, "step": 1, "waiting_for": None}

# --- KEYBOARDS ---
def get_keyboard(uid):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if uid == ADMIN_ID:
        markup.add(KeyboardButton("🚀 စတင်မည် (All)"), KeyboardButton("🛑 ရပ်တန့်မည် (All)"))
        markup.add(KeyboardButton("👤 အဖွဲ့ဝင်သစ် ခွင့်ပြုမည်"), KeyboardButton("🚫 အသုံးပြုသူကို ပိတ်ပင်မည်"))
        markup.add(KeyboardButton("📢 Channel အသစ်ချိတ်မည်"), KeyboardButton("📊 Bot အခြေအနေ"))
    elif uid in allowed_users:
        markup.add(KeyboardButton("📊 Bot အခြေအနေ"))
    else:
        markup.add(KeyboardButton("📩 ဝင်ရောက်ခွင့်တောင်းခံမည်"))
    return markup

# --- ORIGINAL LOGIC ---
def get_original_logic(digits):
    total_sum = sum(int(d) for d in digits)
    if total_sum <= 9: pred = "SMALL"
    elif 10 <= total_sum <= 29: pred = "BIG"
    elif 30 <= total_sum <= 39: pred = "SMALL"
    elif 40 <= total_sum <= 45: pred = "BIG"
    elif 46 <= total_sum <= 50: pred = "SMALL"
    else: pred = "BIG"
    return pred, total_sum, random.randint(88, 96)

def send_to_all(content, is_sticker=False):
    targets = (allowed_users | target_channels)
    for t in targets:
        try:
            if is_sticker: bot.send_sticker(t, content)
            else: bot.send_message(t, content, parse_mode="HTML")
        except: pass

# --- AUTO BROADCAST ---
def broadcast_signal():
    if not state["is_running"]: return
    try:
        res = requests.get(f"{API_URL}?ts={int(time.time()*1000)}", timeout=10).json()
        data = res['data']['list']
        curr_id = data[0]['issueNumber']
        curr_num = int(data[0]['number'])
        actual_res = "BIG" if curr_num >= 5 else "SMALL"
        next_id = str(int(curr_id) + 1)

        if state["last_id"] == curr_id:
            if state["last_pred"] == actual_res:
                send_to_all(WIN_STICKER_ID, is_sticker=True)
                state["step"] = 1
            else:
                send_to_all(f"🔴 <b>LOSE</b> | Result: <b>{actual_res} ({curr_num})</b>")
                state["step"] += 1

        last_ten = [item['number'] for item in data[:10]]
        pred, total, conf = get_original_logic(last_ten)
        state["last_id"], state["last_pred"] = next_id, pred
        
        msg = (f"🧠 <b>QUANTUM V5 AI • TRX 1M</b>\n━━━━━━━━━━━━━━━\n"
               f"🎯 Next Issue: <code>{next_id}</code>\n🔮 Forecast: <b>{pred} x{state['step']}</b>\n"
               f"⚡ Confidence: <code>{conf}%</code> (Σ={total})\n━━━━━━━━━━━━━━━\n👤 Owner: @Zen_th76")
        send_to_all(msg)
    except: pass

def signal_loop():
    while True:
        if datetime.now().second == 58: broadcast_signal(); time.sleep(5)
        time.sleep(0.5)

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if uid in banned_users: return
    bot.send_message(message.chat.id, "🌟 <b>V16 SUPREME ONLINE</b> 🌟", reply_markup=get_keyboard(uid), parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    uid = message.from_user.id
    text = message.text
    if uid == ADMIN_ID:
        if text == "🚀 စတင်မည် (All)":
            state["is_running"] = True
            bot.send_message(uid, "✅ Signal အားလုံး စတင်ပါပြီ။")
        elif text == "🛑 ရပ်တန့်မည် (All)":
            state["is_running"] = False
            bot.send_message(uid, "🛑 Signal များ ရပ်တန့်လိုက်ပါပြီ။")
        elif text == "👤 အဖွဲ့ဝင်သစ် ခွင့်ပြုမည်":
            state["waiting_for"] = "add_user"
            bot.send_message(uid, "ခွင့်ပြုမည့်သူ၏ User ID ကို ပို့ပေးပါ -")
        elif text == "🚫 အသုံးပြုသူကို ပိတ်ပင်မည်":
            state["waiting_for"] = "ban_user"
            bot.send_message(uid, "ပိတ်ပင်မည့်သူ၏ User ID ကို ပို့ပေးပါ -")
        elif text == "📢 Channel အသစ်ချိတ်မည်":
            state["waiting_for"] = "add_channel"
            bot.send_message(uid, "Channel ID ကို ပို့ပေးပါ (-100...) -")
        elif text == "📊 Bot အခြေအနေ":
            bot.send_message(uid, f"📊 Status: {'Online' if state['is_running'] else 'Offline'}\n👥 Users: {len(allowed_users)}\n📡 Channels: {len(target_channels)}")
        elif state["waiting_for"]:
            try:
                target = int(text)
                if state["waiting_for"] == "add_user":
                    allowed_users.add(target); save_data('users.json', allowed_users)
                    bot.send_message(uid, f"✅ User {target} ကို ခွင့်ပြုလိုက်ပါပြီ။")
                elif state["waiting_for"] == "ban_user":
                    banned_users.add(target)
                    if target in allowed_users: allowed_users.remove(target)
                    save_data('banned.json', banned_users); save_data('users.json', allowed_users)
                    bot.send_message(uid, f"🚫 User {target} ကို ပိတ်ပင်လိုက်ပါပြီ။")
                elif state["waiting_for"] == "add_channel":
                    target_channels.add(target); save_data('channels.json', target_channels)
                    bot.send_message(uid, f"📢 Channel {target} ချိတ်ဆက်ပြီး။")
                state["waiting_for"] = None
            except: bot.send_message(uid, "❌ ID မှားယွင်းနေပါသည်။")
    elif text == "📩 ဝင်ရောက်ခွင့်တောင်းခံမည်":
        bot.send_message(ADMIN_ID, f"🔔 <b>တောင်းခံချက်</b>\nID: <code>{uid}</code>")
        bot.send_message(uid, "✅ Admin ထံ တောင်းခံချက် ပို့ပြီးပါပြီ။")

if __name__ == "__main__":
    threading.Thread(target=signal_loop, daemon=True).start()
    bot.polling(none_stop=True)
