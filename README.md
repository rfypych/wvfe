# WVFE - Web Vulnerability Finder and Exploiter

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12-blue)
![Framework](https://img.shields.io/badge/framework-Flask%20%26%20React-cyan)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

WVFE is an integrated web application security tool designed to automate the process of finding and demonstrating common vulnerabilities in websites. It serves as both a practical audit tool for developers and an educational platform for understanding web security.

## 🚀 Project Overview

This tool was created to address the growing need for accessible and automated web security testing. WVFE allows users to perform security scans on their web applications, identify potential weaknesses, and receive clear, actionable reports.

### Key Features
- **User Authentication:** Secure registration and login system for users.
- **Web Crawler:** Automatically discovers links and forms on the target site to identify attack surfaces.
- **Vulnerability Scanner Modules:**
  - **Sensitive Data Exposure:** Scans for publicly accessible sensitive files (e.g., `.env`, `.git/config`).
  - **SQL Injection (SQLi):** Detects error-based SQL injection vulnerabilities in URL parameters and forms.
  - **Cross-Site Scripting (XSS):** Detects reflected XSS vulnerabilities in URL parameters and forms.
- **Scan Management Dashboard:** An intuitive interface to start new scans, view scan history, and examine detailed vulnerability reports.

## 🛠️ Technology Stack

- **Backend:** Python 3.12 with **Flask**
- **Frontend:** JavaScript with **React.js**
- **Database:** **MySQL**
- **Architecture:** Monorepo

## ⚙️ Setup and Installation

Follow these steps to get your local development environment set up.

### Prerequisites
- Python 3.10+
- Node.js and npm
- A running MySQL server

### 1. Clone the Repository
```bash
git clone <repository_url>
cd wvfe-project
```

### 2. Backend Setup
The backend is located in the `/backend` directory.

**a. Create a Virtual Environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

**b. Configure Environment Variables**
Copy the example environment file and update it with your database credentials.
```bash
cp backend/.env.example backend/.env
# Open backend/.env and edit the following variables:
# DB_HOST=your_db_host
# DB_USER=your_db_user
# DB_PASSWORD=your_db_password
# DB_NAME=your_db_name
# SECRET_KEY=generate_a_random_secret_key
```

**c. Install Dependencies**
```bash
pip install -r backend/requirements.txt
```

### 3. Frontend Setup
The frontend is located in the `/frontend` directory.

**a. Navigate to the Frontend Directory**
```bash
cd frontend
```

**b. Install Dependencies**
```bash
npm install
```
```bash
cd .. # Return to the root directory
```

## ▶️ Usage

The backend and frontend servers must be run separately in two different terminal sessions.

### 1. Run the Backend Server
Make sure you are in the project root directory and have your Python virtual environment activated.
```bash
python backend/app.py
```
The Flask server will start on `http://127.0.0.1:5001`. The database tables will be created automatically on the first run.

### 2. Run the Frontend Server
Open a new terminal and navigate to the `/frontend` directory.
```bash
cd frontend
npm start
```
The React development server will start, and your browser should automatically open to `http://localhost:3000`.

You can now register a new user, log in, and start scanning from the dashboard.

## ⚠️ Disclaimer

This tool is intended for educational purposes and for authorized security testing only. **DO NOT** use this tool to scan any website for which you do not have explicit, written permission from the owner. Unauthorized scanning is illegal. The developers of this tool are not responsible for any misuse or damage caused by this program.
