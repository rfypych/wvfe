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
Make sure you are in the project root directory. You can run the development server (for testing) or the production server (for deployment).

**For Development:**
```bash
# Make sure your virtual environment is activated
source backend/venv/bin/activate
python backend/app.py
```
The Flask development server will start on `http://127.0.0.1:5001`.

**For Production (Recommended):**
Use the deployment script to start the Gunicorn server.
```bash
chmod +x deploy.sh
./deploy.sh start
```
This will activate the correct environment and run the server on `http://127.0.0.1:5001`.

### 2. Run the Frontend Server
Open a new terminal and navigate to the `/frontend` directory.
```bash
cd frontend
npm start
```
The React development server will start, and your browser should automatically open to `http://localhost:3000`.

You can now register a new user, log in, and start scanning from the dashboard.

## 🚀 Easy Deployment with Script (Recommended)

To simplify the deployment process, a helper script `deploy.sh` is provided. This script will automate dependency installation, build the frontend, and generate the necessary server configurations for you.

### How to Use
1. **Make the script executable:**
   ```bash
   chmod +x deploy.sh
   ```

2. **Run the script:**
   ```bash
   ./deploy.sh
   ```

3. **Follow the on-screen instructions:**
   - The script will first build the backend and frontend.
   - It will then ask for your domain name.
   - Finally, it will print the exact instructions and configuration snippets you need to copy and paste into your aaPanel website settings.

## Manual Deployment to aaPanel with Apache

Deploying a modern web application with a separate frontend and backend requires a few specific steps. Here is a guide to deploying WVFE on a server managed by aaPanel with Apache.

### 1. Backend Deployment (Flask API)

The backend needs to be run as a persistent service using a WSGI server like Gunicorn. Apache will then act as a reverse proxy, forwarding API requests to the Gunicorn service.

**a. Upload and Prepare Backend**
   - Upload the entire `/backend` folder to your server (e.g., to `/www/wwwroot/yourdomain.com/backend`).
   - Set up your Python environment using **aaPanel's Python Manager**. Create a new virtual environment for the project.
   - Install dependencies: `pip install -r /www/wwwroot/yourdomain.com/backend/requirements.txt`.
   - Make sure your `.env` file is configured with your production database credentials.

**b. Run with Gunicorn**
   - You can run Gunicorn directly from the command line to test it. Navigate to your backend directory and run:
     ```bash
     gunicorn --bind 127.0.0.1:5001 app:app
     ```
   - For a persistent service, it's recommended to use a process manager like `systemd` or set it up as a project in aaPanel's Python Manager.

**c. Configure Reverse Proxy in aaPanel**
   1. In aaPanel, go to the **Website** menu and select the site you are using.
   2. Click on **Reverse proxy**.
   3. Click **Add reverse proxy**.
   4. Set a **Proxy name** (e.g., "api-proxy").
   5. Set the **Target URL** to `http://127.0.0.1:5001`.
   6. Set the **Proxy Directory** to `/api`. This means any requests to `yourdomain.com/api` will be forwarded to your Flask app.
   7. Save the configuration.

### 2. Frontend Deployment (React App)

The React frontend must be "built" into static HTML, CSS, and JavaScript files, which Apache can then serve directly.

**a. Build the React App**
   - Upload the entire `/frontend` folder to your server (e.g., to `/www/wwwroot/yourdomain.com/frontend`).
   - Navigate to the frontend directory: `cd /www/wwwroot/yourdomain.com/frontend`.
   - Install dependencies: `npm install`.
   - Run the build script: `npm run build`. This will create a `/frontend/build` directory containing all the static assets.

**b. Configure Apache in aaPanel**
   1. In aaPanel, go to the **Website** menu and select the same site.
   2. Set the **Website directory** to point to the `build` folder of your frontend (e.g., `/www/wwwroot/yourdomain.com/frontend/build`).
   3. Go to **URL rewrite**.
   4. Add the following rewrite rule. This is crucial for a Single-Page Application (SPA) as it directs all non-file requests to `index.html`, allowing React Router to handle them.
      ```apacheconf
      <IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteCond %{REQUEST_FILENAME} !-l
        RewriteRule . /index.html [L]
      </IfModule>
      ```
   5. Save the configuration.

Your application should now be live. The root domain will serve the React frontend, and any API calls made by the frontend to `/api/...` will be correctly proxied to the Flask backend.

## ⚠️ Disclaimer

This tool is intended for educational purposes and for authorized security testing only. **DO NOT** use this tool to scan any website for which you do not have explicit, written permission from the owner. Unauthorized scanning is illegal. The developers of this tool are not responsible for any misuse or damage caused by this program.
