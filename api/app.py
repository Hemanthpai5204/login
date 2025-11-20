from flask import Flask, render_template, request, jsonify, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use env var for production

# Database configuration - using SQLite for Vercel compatibility
DATABASE = os.environ.get('DATABASE', '/tmp/flask_app.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create database and table if not exists
def create_database_and_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# create_database_and_table()  # Commented out to avoid import-time execution

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    create_database_and_table()  # Create table if not exists
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    hashed_password = generate_password_hash(password)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'User registered successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 400
    except sqlite3.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    create_database_and_table()  # Create table if not exists
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and check_password_hash(result['password'], password):
            session['username'] = username
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    except sqlite3.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500

@app.route('/login', methods=['GET'])
def check_login():
    if 'username' in session:
        return jsonify({'message': 'You are logged in', 'username': session['username']})
    else:
        return jsonify({'message': 'Not logged in'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logout successful'})

# Vercel requires this for serverless
def handler(event, context):
    return app(event, context)
