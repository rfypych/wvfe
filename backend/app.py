# Main application file for WVFE
import os
import time
import threading
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import mysql.connector
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from scanners.sensitive_file_scanner import check_sensitive_files

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
        print("Could not connect to the database to initialize.")
        return

    cursor = conn.cursor()
    print("Creating database tables if they don't exist...")

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Scans Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            target_url VARCHAR(2048) NOT NULL,
            status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Vulnerabilities Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vulnerabilities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            scan_id INT NOT NULL,
            type VARCHAR(100) NOT NULL,
            url VARCHAR(2048) NOT NULL,
            payload VARCHAR(2048),
            details TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialization complete.")

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

# --- Real Scanner Logic ---
def run_real_scan(app_context, scan_id, target_url):
    """
    This function runs in a background thread to perform the actual scan.
    """
    with app_context:
        print(f"Starting real scan for scan_id: {scan_id} on {target_url}")
        conn = get_db_connection()
        if not conn:
            print(f"Scan {scan_id} failed: could not connect to DB")
            return

        try:
            cursor = conn.cursor()
            # 1. Set status to 'running'
            cursor.execute("UPDATE scans SET status = 'running' WHERE id = %s", (scan_id,))
            conn.commit()

            # 2. Run all scanner modules
            # For now, we only have one module. In the future, we can loop through them.
            found_vulns = check_sensitive_files(target_url)

            # 3. Save vulnerabilities to the database
            for vuln in found_vulns:
                cursor.execute(
                    "INSERT INTO vulnerabilities (scan_id, type, url, payload, details) VALUES (%s, %s, %s, %s, %s)",
                    (scan_id, vuln['type'], vuln['url'], vuln['payload'], vuln['details'])
                )

            # 4. Set status to 'completed'
            cursor.execute("UPDATE scans SET status = 'completed' WHERE id = %s", (scan_id,))
            conn.commit()
            print(f"Real scan {scan_id} completed. Found {len(found_vulns)} vulnerabilities.")

        except Exception as e:
            print(f"An error occurred during scan {scan_id}: {e}")
            # In case of any error during the scan, mark as 'failed'
            if conn.is_connected():
                cursor = conn.cursor()
                cursor.execute("UPDATE scans SET status = 'failed' WHERE id = %s", (scan_id,))
                conn.commit()
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

# --- Scan Management API ---
@app.route('/api/scans', methods=['POST'])
@login_required
def start_scan():
    data = request.get_json()
    target_url = data.get('target_url')

    if not target_url:
        return jsonify({"status": "error", "message": "Target URL is required."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed."}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO scans (user_id, target_url) VALUES (%s, %s)",
            (current_user.id, target_url)
        )
        conn.commit()
        scan_id = cursor.lastrowid
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    # Run the real scanner in a background thread
    scan_thread = threading.Thread(
        target=run_real_scan,
        args=(app.app_context(), scan_id, target_url)
    )
    scan_thread.start()

    return jsonify({
        "status": "success",
        "message": "Scan started successfully.",
        "scan_id": scan_id
    }), 202

@app.route('/api/scans', methods=['GET'])
@login_required
def get_scans():
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed."}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, target_url, status, created_at FROM scans WHERE user_id = %s ORDER BY created_at DESC",
            (current_user.id,)
        )
        scans = cursor.fetchall()
    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(scans)

@app.route('/api/scans/<int:scan_id>', methods=['GET'])
@login_required
def get_scan_details(scan_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed."}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # First, get the scan details and verify ownership
        cursor.execute("SELECT * FROM scans WHERE id = %s AND user_id = %s", (scan_id, current_user.id))
        scan = cursor.fetchone()
        if not scan:
            return jsonify({"status": "error", "message": "Scan not found or access denied."}), 404

        # Then, get the vulnerabilities for that scan
        cursor.execute("SELECT * FROM vulnerabilities WHERE scan_id = %s", (scan_id,))
        vulnerabilities = cursor.fetchall()
        scan['vulnerabilities'] = vulnerabilities

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": f"Database error: {err}"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify(scan)

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
