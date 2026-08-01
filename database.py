import sqlite3

def init_db():
    conn = sqlite3.connect("konso_lottery.db")
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            type TEXT,
            owner_id INTEGER,
            status TEXT DEFAULT 'available',
            round INTEGER DEFAULT 1
        )
    """)
    
    # Payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            proof TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    # Initialize 1000 tickets if not exist
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE round = 1")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 1001):
            num_str = f"{i:03d}"
            cursor.execute("INSERT INTO tickets (number, type, status, round) VALUES (?, 'full', 'available', 1)", (num_str,))
            
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("konso_lottery.db")
