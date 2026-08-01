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
            phone TEXT,
            password TEXT,
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
    email: str
    phone: str
    password: str

class VerifyOTP(BaseModel):
    email: str
    otp: str

class UserLogin(BaseModel):
    email: str
    password: str

class BuyTicketModel(BaseModel):
    email: str
    number: str
    ticket_type: str
    bank_receipt: str

class MessageModel(BaseModel):
    email: str
    message: str

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/admin")
def read_admin():
    return FileResponse("admin.html")

@app.post("/api/register")
def register(data: UserRegister):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email=?", (data.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="ይህ ኢሜል ቀደም ሲል ተመዝግቧል!")
    
    otp = f"{random.randint(1000, 9999)}"
    try:
        cursor.execute(
            "INSERT INTO users (full_name, email, phone, password, otp_code, is_verified) VALUES (?, ?, ?, ?, ?, 0)",
            (data.full_name, data.email, data.phone, data.password, otp)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"status": "success", "message": "ምዝገባ ተሳክቷል", "debug_otp": otp}

@app.post("/api/verify-otp")
def verify_otp(data: VerifyOTP):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND otp_code=?", (data.email, data.otp))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="የተሳሳተ የ OTP ቁጥር!")
    
    cursor.execute("UPDATE users SET is_verified=1, otp_code=NULL WHERE email=?", (data.email,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "አካውንትዎ ጸድቋል!"}

@app.post("/api/login")
def login(data: UserLogin):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (data.email, data.password))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=400, detail="የተሳሳተ ኢሜል ወይም የይለፍ ቃል!")
    if user[5] == 0:
        raise HTTPException(status_code=403, detail="እባክዎ መጀመሪያ አካውንትዎን በ OTP ያረጋግጡ!")
    
    return {"status": "success", "user": {"full_name": user[1], "email": user[2]}}

@app.post("/api/tickets/buy")
def buy_ticket(data: BuyTicketModel):
    if not data.bank_receipt.strip():
        raise HTTPException(status_code=400, detail="እባክዎ የክፍያ ማረጋገጫ ቁጥር (Receipt/Transaction ID) ያስገቡ!")
        
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email=?", (data.email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="ተጠቃሚው አልተገኘም")
    
    owner_id = user[0]
    
    # Check if number already taken
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
def get_user_tickets(email: str):
    conn = sqlite3.connect(DB_Name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT t.* FROM tickets t JOIN users u ON t.owner_id = u.id WHERE u.email = ? ORDER BY t.id DESC", (email,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/message/send")
def send_message(data: MessageModel):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_email, message, created_at) VALUES (?, ?, ?)", 
                   (data.email, data.message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "መልዕክትዎ በተሳካ ሁኔታ ተልኳል!"}

@app.get("/api/admin/tickets")
def admin_get_tickets(secret: str):
    if secret != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    conn = sqlite3.connect(DB_Name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT t.*, u.full_name, u.email, u.phone FROM tickets t JOIN users u ON t.owner_id = u.id ORDER BY t.id DESC")
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
