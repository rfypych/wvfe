# Main application file for WVFE
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import mysql.connector
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# A secret key is needed for session management (e.g., by Flask-Login)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_super_secret_default_key')

# Enable CORS for all routes, allowing credentials to be sent
CORS(app, supports_credentials=True)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return jsonify({"status": "error", "message": "Authorization required."}), 401

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'])
    return None

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# --- Database Initialization ---
def init_db():
    """Creates the database tables."""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# --- Authentication API ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required."}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed."}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
    except mysql.connector.Error as err:
        # 23000 is the integrity error code for duplicates
        if '1062' in str(err): # Duplicate entry
             return jsonify({"status": "error", "message": "Username already exists."}), 409
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"status": "success", "message": "User registered successfully."}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed."}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_data and bcrypt.check_password_hash(user_data['password_hash'], password):
        user = User(id=user_data['id'], username=user_data['username'])
        login_user(user)
        return jsonify({"status": "success", "message": "Logged in successfully."})

    return jsonify({"status": "error", "message": "Invalid username or password."}), 401

@app.route('/api/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"status": "success", "message": "Logged out successfully."})

# --- Main Application Routes ---
@app.route('/')
def index():
    # This will eventually be handled by the React frontend
    return "Welcome to the WVFE API. Please use the frontend to interact with the service."

@app.route('/api/dashboard')
@login_required
def dashboard():
    # A protected route as an example
    return jsonify({
        "status": "success",
        "message": f"Welcome to your dashboard, {current_user.username}!",
        "user": {
            "id": current_user.id,
            "username": current_user.username
        }
    })

if __name__ == '__main__':
    # It's good practice to initialize the DB outside the request flow
    init_db()
    app.run(debug=True, port=5001) # Running on a different port to avoid conflicts with React dev server
