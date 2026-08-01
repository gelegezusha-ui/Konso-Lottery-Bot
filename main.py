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
            otp_code TEXT,
            balance INTEGER DEFAULT 0
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
            created_at TEXT NOT NULL
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
    
    return {"status": "success", "user": {"full_name": user[1], "email": user[2], "balance": user[7]}}

@app.post("/api/tickets/buy")
def buy_ticket(data: BuyTicketModel):
    conn = sqlite3.connect(DB_Name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email=?", (data.email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="ተጠቃሚው አልተገኘም")
    
    owner_id = user[0]
    tx_ref = f"WEB-{random.randint(100000, 999999)}"
    amount = PRICE_FULL if data.ticket_type == "FULL" else PRICE_HALF

    try:
        cursor.execute(
            "INSERT INTO tickets (number, type, status, owner_id, tx_ref, created_at) VALUES (?, ?, 'PENDING', ?, ?, ?)",
            (data.number, data.ticket_type, owner_id, tx_ref, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="ይህ የዕጣ ቁጥር አስቀድሞ ተይዟል!")
    conn.close()
    return {"status": "success", "tx_ref": tx_ref, "amount": amount}

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
