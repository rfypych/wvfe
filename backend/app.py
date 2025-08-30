# Main application file for WVFE
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import mysql.connector

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

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
        # In a real app, you'd want to log this error.
        print(f"Error: {err}")
        return None

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    url = request.form['url']
    # For now, just returning the URL. DB logic will be added later.
    return f"Scanning {url}..."

@app.route('/db_test')
def db_test():
    """A simple route to test the database connection."""
    conn = get_db_connection()
    if conn:
        try:
            conn.close()
            return jsonify({"status": "success", "message": "Database connection successful."})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "error", "message": "Database connection failed."}), 500


if __name__ == '__main__':
    app.run(debug=True)
