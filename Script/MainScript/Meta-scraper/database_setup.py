import sqlite3

def create_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        email TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_table()
