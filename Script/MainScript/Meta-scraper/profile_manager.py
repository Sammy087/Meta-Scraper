# profile_manager.py
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def create_profile(username, password, email):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(password)
        cursor.execute('''
        INSERT INTO users (username, password, email)
        VALUES (?, ?, ?)
        ''', (username, hashed_password, email))
        conn.commit()
        print(f"Profile for {username} created successfully.")
    except sqlite3.IntegrityError:
        print("Username already exists.")
    finally:
        conn.close()

def login(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    record = cursor.fetchone()

    if record and check_password_hash(record[0], password):
        print(f"Login successful. Welcome, {username}!")
        return True
    else:
        print("Login failed. Invalid username or password.")
        return False

def delete_profile(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()

    if cursor.rowcount > 0:
        print(f"Profile for {username} deleted successfully.")
    else:
        print(f"Profile for {username} not found.")

    conn.close()

if __name__ == "__main__":
    # Example usage
    create_profile('testuser', 'password123', 'testuser@example.com')
    login('testuser', 'password123')
    delete_profile('testuser')
