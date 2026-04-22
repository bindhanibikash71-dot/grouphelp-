import sqlite3
import os
import datetime

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users, Monetization, Gamification
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, lang TEXT DEFAULT 'en',
                  tier TEXT DEFAULT 'free', limits INTEGER DEFAULT 50, xp INTEGER DEFAULT 0,
                  level INTEGER DEFAULT 1, is_banned BOOLEAN DEFAULT 0, joined_at TIMESTAMP)''')
    
    # Group & Moderation Tracker
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (chat_id INTEGER PRIMARY KEY, title TEXT, is_active BOOLEAN DEFAULT 1, 
                  auto_ai BOOLEAN DEFAULT 1, strict_mod BOOLEAN DEFAULT 0)''')
                  
    # Admin Logs & System
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER KEY AUTOINCREMENT, user_id INTEGER, action TEXT, details TEXT, timestamp TIMESTAMP)''')

    # App Settings
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Redeem Codes
    c.execute('''CREATE TABLE IF NOT EXISTS codes
                 (code TEXT PRIMARY KEY, reward_type TEXT, amount INTEGER, used_by INTEGER DEFAULT NULL)''')

    # Seed Default settings
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('sys_prompt', 'You are an advanced helpful AI.')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('mode', 'Friendly')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('ai_temp', '0.7')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maint_mode', '0')")
    
    conn.commit()
    conn.close()

def execute(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute(query, params)

def fetch(query, params=(), one=False):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(query, params)
        return cur.fetchone() if one else cur.fetchall()

def log_event(user_id, action, details=""):
    execute("INSERT INTO logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)", 
            (user_id, action, details, datetime.datetime.now()))
