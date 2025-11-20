from flask import Flask, render_template, request, jsonify, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use env var for production

# Database configuration - for Vercel, use environment variables
db_config = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'jeevanpai2006'),
    'database': os.environ.get('DB_NAME', 'flask_app')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Create database and table if not exists
def create_database_and_table():
    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        cursor.execute('CREATE DATABASE IF NOT EXISTS {}'.format(db_config['database']))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Database creation error: {err}")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Table creation error: {err}")

create_database_and_table()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    hashed_password = generate_password_hash(password)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'User registered successfully'})
    except mysql.connector.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 400
    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password required'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and check_password_hash(result[0], password):
            session['username'] = username
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    except mysql.connector.Error as err:
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
