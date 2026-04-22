import telebot
import os
import datetime
from telebot.types import Message
from database import execute, fetch, log_event
from ai_engine import generate_ai_response, moderate_text

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"), threaded=False)

def check_user_db(msg: Message):
    uid, uname = msg.from_user.id, msg.from_user.username
    user = fetch("SELECT * FROM users WHERE user_id=?", (uid,), one=True)
    if not user:
        execute("INSERT INTO users (user_id, username, joined_at) VALUES (?, ?, ?)", 
                (uid, uname, datetime.datetime.now()))
        user = fetch("SELECT * FROM users WHERE user_id=?", (uid,), one=True)
    return user

@bot.message_handler(commands=['start', 'help', 'id', 'plan', 'leaderboard', 'redeem'])
def super_commands(message):
    u = check_user_db(message)
    cmd = message.text.split()[0].replace('/', '')
    
    if cmd == 'id':
        bot.reply_to(message, f"🎫 Your Telegram ID: `{u['user_id']}`\n🌟 Tier: {u['tier'].upper()}\n🔥 Lvl: {u['level']} | XP: {u['xp']}", parse_mode="Markdown")
    
    elif cmd == 'start' or cmd == 'help':
        bot.reply_to(message, "🚀 *Next-Gen SaaS Bot Active*\nI respond via mentions or replies. Powered by mistral AI.", parse_mode="Markdown")
        
    elif cmd == 'leaderboard':
        tops = fetch("SELECT username, level, xp FROM users ORDER BY xp DESC LIMIT 5")
        text = "🏆 *Top Users*\n"
        for i, t in enumerate(tops):
            text += f"{i+1}. @{t['username']} - Lvl {t['level']} ({t['xp']} XP)\n"
        bot.reply_to(message, text, parse_mode="Markdown")

    elif cmd == 'redeem':
        parts = message.text.split()
        if len(parts) == 2:
            code = fetch("SELECT * FROM codes WHERE code=? AND used_by IS NULL", (parts[1],), one=True)
            if code:
                execute("UPDATE codes SET used_by=? WHERE code=?", (u['user_id'], parts[1]))
                execute("UPDATE users SET tier=?, limits=limits+? WHERE user_id=?", (code['reward_type'], code['amount'], u['user_id']))
                bot.reply_to(message, f"✅ Successfully redeemed! Upgraded to {code['reward_type'].upper()}.")
            else:
                bot.reply_to(message, "❌ Invalid or already used code.")

@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_text(message):
    u = check_user_db(message)
    
    # Admin Master Control check
    maint = fetch("SELECT value FROM settings WHERE key='maint_mode'", one=True)["value"]
    if maint == '1': return
    
    # Restrict replies in groups to replies or mentions
    is_group = message.chat.type in ['group', 'supergroup']
    if is_group:
        g = fetch("SELECT * FROM groups WHERE chat_id=?", (message.chat.id,), one=True)
        if not g:
            execute("INSERT INTO groups (chat_id, title) VALUES (?, ?)", (message.chat.id, message.chat.title))
        
        # Check moderation
        if moderate_text(message.text):
            bot.delete_message(message.chat.id, message.id)
            bot.send_message(message.chat.id, f"⚠️ @{message.from_user.username}, your message contained restricted phrases.")
            return

        bot_mentioned = ('@'+bot.get_me().username) in message.text
        is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        if not (bot_mentioned or is_reply):
            return

    # User Checks & Monetization
    if u['is_banned']: return
    if u['limits'] <= 0 and u['tier'] == 'free':
        bot.reply_to(message, "💸 Free limits exhausted! Type /buy or /plan.")
        return

    # Show simulated "typing"
    bot.send_chat_action(message.chat.id, 'typing')
    
    reply_text = generate_ai_response(message.text, u['lang'])
    bot.reply_to(message, reply_text)
    
    # Update Gamification & DB
    new_xp = u['xp'] + 5
    new_lvl = int(new_xp ** 0.5 * 0.5) + 1
    new_limit = u['limits'] - 1 if u['tier'] != 'vip' else u['limits'] # VIP Infinite
    
    execute("UPDATE users SET xp=?, level=?, limits=? WHERE user_id=?", (new_xp, new_lvl, new_limit, u['user_id']))
    log_event(u['user_id'], 'ai_prompt')

def setup_webhook(app_url):
    bot.remove_webhook()
    time.sleep(1)
    url = f"{app_url}/webhook"
    bot.set_webhook(url=url)
