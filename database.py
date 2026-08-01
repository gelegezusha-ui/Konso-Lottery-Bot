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
            balance REAL DEFAULT 0.0,
            referred_by INTEGER,
            language TEXT DEFAULT 'am',
            age_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tickets table (001 to 1000 for Round 1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT,
            type TEXT, -- 'full' or 'half'
            owner_id INTEGER,
            status TEXT DEFAULT 'available', -- 'available', 'pending', 'sold'
            round INTEGER DEFAULT 5
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
            status TEXT DEFAULT 'pending' -- 'pending', 'approved', 'rejected'
        )
    """)
    
    # Initialize 1000 tickets for Round 5 if not exist
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE round = 5")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 1001):
            num_str = f"{i:03d}"
            cursor.execute("INSERT INTO tickets (number, type, owner_id, status, round) VALUES (?, 'full', NULL, 'available', 5)", (num_str,))
            
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("konso_lottery.db")
