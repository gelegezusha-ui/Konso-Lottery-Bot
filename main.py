import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Konso Lottery Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_SECRET_KEY = "KonsoLotteryAdmin2026SecureKey!"
PRICE_FULL = 500
PRICE_HALF = 250
DB_Name = "konso_lottery.db"

def db_init():
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            pin_code TEXT,
            is_verified INTEGER DEFAULT 0,
            otp_code TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            tx_ref TEXT UNIQUE NOT NULL,
            bank_receipt TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            message TEXT,
            admin_reply TEXT DEFAULT '',
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT,
            position TEXT,
            prize INTEGER
        )
    ''')
    conn.commit()
    conn.close()

db_init()

class UserRegister(BaseModel):
    full_name: str
    phone: str
    email: str
    pin_code: str

class VerifyOTP(BaseModel):
    phone: str
    otp: str

class UserLogin(BaseModel, extra="allow"):
    phone: str
    pin_code: str

class BuyTicketModel(BaseModel):
    phone: str
    number: str
    ticket_type: str
    bank_receipt: str

class MessageModel(BaseModel):
    phone: str
    message: str

class AdminReplyModel(BaseModel):
    msg_id: int
    reply: str

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/admin")
def read_admin():
    return FileResponse("admin.html")

@app.post("/api/register")
def register(data: UserRegister):
    if len(data.pin_code) != 6 or not data.pin_code.isdigit():
        raise HTTPException(status_code=400, detail="ሚስጥር ቁጥሩ (PIN) ጥንካሬውን የጠበቀ እና በትክክል 6 አሃዝ መሆን አለበት!")

    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE phone=? OR email=?", (data.phone, data.email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="ይህ ስልክ ቁጥር ወይም ኢሜል ቀደም ሲል ተመዝግቧል!")
    
    otp = f"{random.randint(100000, 999999)}"
    try:
        cursor.execute(
            "INSERT INTO users (full_name, phone, email, pin_code, otp_code, is_verified) VALUES (?, ?, ?, ?, ?, 0)",
            (data.full_name, data.phone, data.email, data.pin_code, otp)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"status": "success", "message": "የ OTP ቁጥር ወደ ስልክዎ ተልኳል", "sms_otp": otp}

@app.post("/api/verify-otp")
def verify_otp(data: VerifyOTP):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone=? AND otp_code=?", (data.phone, data.otp))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="የተሳሳተ የ OTP ቁጥር!")
    
    cursor.execute("UPDATE users SET is_verified=1, otp_code=NULL WHERE phone=?", (data.phone,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "አካውንትዎ በስልክ ቁጥርዎ ጸድቋል!"}

@app.post("/api/login")
def login(data: UserLogin):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone=? AND pin_code=?", (data.phone, data.pin_code))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=400, detail="የተሳሳተ ስልክ ቁጥር ወይም ሚስጥር ቁጥር (PIN)!")
    if user[5] == 0:
        raise HTTPException(status_code=403, detail="እባክዎ መጀመሪያ አካውንትዎን በ OTP ያረጋግጡ!")
    
    return {"status": "success", "user": {"full_name": user[1], "phone": user[2], "email": user[3]}}

@app.post("/api/tickets/buy")
def buy_ticket(data: BuyTicketModel):
    if not data.bank_receipt.strip():
        raise HTTPException(status_code=400, detail="እባክዎ የክፍያ ማረጋገጫ ቁጥር (Receipt/Transaction ID) ያስገቡ!")
        
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE phone=?", (data.phone,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="ተጠቃሚው አልተገኘም")
    
    owner_id = user[0]
    
    cursor.execute("SELECT id FROM tickets WHERE number=?", (data.number,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="ይህ የዕጣ ቁጥር አስቀድሞ ተይዟል!")

    tx_ref = f"KONSO-{random.randint(100000, 999999)}"
    amount = PRICE_FULL if data.ticket_type == "FULL" else PRICE_HALF

    try:
        cursor.execute(
            "INSERT INTO tickets (number, type, status, owner_id, tx_ref, bank_receipt, created_at) VALUES (?, ?, 'PENDING', ?, ?, ?, ?)",
            (data.number, data.ticket_type, owner_id, tx_ref, data.bank_receipt, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    conn.close()
    return {"status": "success", "tx_ref": tx_ref, "amount": amount}

@app.get("/api/user/tickets")
def get_user_tickets(phone: str):
    conn = sqlite3.connect(DB_Name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT t.* FROM tickets t JOIN users u ON t.owner_id = u.id WHERE u.phone = ? ORDER BY t.id DESC", (phone,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/message/send")
def send_message(data: MessageModel):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_email, message, created_at) VALUES (?, ?, ?)", 
                   (data.phone, data.message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "መልዕክትዎ በተሳካ ሁኔታ ተልኳል!"}

@app.get("/api/user/messages")
def get_user_messages(phone: str):
    conn = sqlite3.connect(DB_Name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE user_email = ? ORDER BY id DESC", (phone,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/admin/tickets")
def admin_get_tickets(secret: str):
    if secret != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_Name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT t.*, u.full_name, u.phone, u.email FROM tickets t JOIN users u ON t.owner_id = u.id ORDER BY t.id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/admin/messages")
def admin_get_messages(secret: str):
    if secret != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_Name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/admin/reply")
def admin_reply(data: AdminReplyModel, secret: str):
    if secret != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET admin_reply=? WHERE id=?", (data.reply, data.msg_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/admin/approve/{tx_ref}")
def admin_approve(tx_ref: str, secret: str):
    if secret != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET status='PAID' WHERE tx_ref=?", (tx_ref,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/admin/draw")
def admin_draw(secret: str):
    if secret != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT number FROM tickets WHERE status='PAID'")
    paid_tickets = [r[0] for r in cursor.fetchall()]
    
    if len(paid_tickets) < 1:
        conn.close()
        raise HTTPException(status_code=400, detail="ክፍያው የጸደቀ ቲኬት የለም!")
    
    winners_data = [
        ("1ኛ አሸናፊ", 400000),
        ("2ኛ አሸናፊ", 10000),
        ("3ኛ አሸናፊ", 5000),
        ("4ኛ አሸናፊ", 2500),
        ("5ኛ አሸናፊ", 1000),
        ("6ኛ አሸናፊ", 500)
    ]
    
    cursor.execute("DELETE FROM winners")
    drawn = random.sample(paid_tickets, min(len(paid_tickets), len(winners_data)))
    
    for idx, t_num in enumerate(drawn):
        pos, prize = winners_data[idx]
        cursor.execute("INSERT INTO winners (ticket_number, position, prize) VALUES (?, ?, ?)", (t_num, pos, prize))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": "ዕጣው በተሳካ ሁኔታ ወጥቷል!"}
