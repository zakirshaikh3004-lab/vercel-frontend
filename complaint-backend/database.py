import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            role TEXT,
            password TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            department_id INTEGER,
            priority TEXT,
            status TEXT,
            anonymous BOOLEAN,
            user_id INTEGER,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Insert sample data
    departments = ['Hostel', 'IT', 'Classroom', 'Mess', 'Library']
    for dept in departments:
        c.execute('INSERT OR IGNORE INTO departments (name) VALUES (?)', (dept,))
    
    # Create admin user
    admin_password = pwd_context.hash("admin123")
    c.execute('INSERT OR IGNORE INTO users (email, name, role, password) VALUES (?, ?, ?, ?)',
              ('admin@college.edu', 'Admin', 'admin', admin_password))
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('complaints.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn