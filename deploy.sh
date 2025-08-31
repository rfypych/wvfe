#!/bin/bash

# A script to automate the build process for the WVFE project.

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting WVFE Deployment Helper...${NC}"

# --- Step 1: Backend Setup ---
echo -e "\n${YELLOW}--- Setting up Backend ---${NC}"
cd backend

# Check if virtual environment exists, if not, create it.
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please ensure python3-venv is installed."
        exit 1
    fi
fi

# Activate virtual environment and install dependencies
echo "Installing backend dependencies from requirements.txt..."
source venv/bin/activate
pip install -r requirements.txt
deactivate

echo -e "${GREEN}Backend setup complete.${NC}"
cd ..


# --- Step 2: Frontend Setup ---
echo -e "\n${YELLOW}--- Setting up Frontend ---${NC}"
cd frontend

echo "Installing frontend dependencies with npm..."
npm install

echo "Building React app for production..."
npm run build

if [ ! -d "build" ]; then
    echo "Frontend build failed. Please check for errors from 'npm run build'."
    exit 1
fi

echo -e "${GREEN}Frontend setup and build complete.${NC}"
cd ..

echo -e "\n${GREEN}Build process finished!${NC}"


# --- Step 3: Generate aaPanel Configurations ---
echo -e "\n${YELLOW}--- Generating aaPanel Configurations ---${NC}"
echo "Please enter the domain you are using in aaPanel (e.g., wvfe.yourdomain.com):"
read -p "Domain Name: " DOMAIN_NAME

if [ -z "$DOMAIN_NAME" ]; then
    echo "No domain name entered. Skipping config generation."
    exit 1
fi

# Get the absolute path to the project directory
PROJECT_PATH=$(pwd)

# --- Generate Reverse Proxy Config ---
REVERSE_PROXY_CONFIG="
# Paste this into your aaPanel Website -> Reverse proxy -> Add reverse proxy -> Config file

#Proxy-Start
<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass /api http://127.0.0.1:5001
    ProxyPassReverse /api http://127.0.0.1:5001
</IfModule>
#Proxy-End
"

# --- Generate URL Rewrite Config ---
REWRITE_CONFIG="
# Paste this into your aaPanel Website -> URL rewrite -> Config file
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule . /index.html [L]
</IfModule>
"

echo -e "\n\n${GREEN}================== DEPLOYMENT INSTRUCTIONS ==================${NC}"
echo -e "\n${YELLOW}1. Configure Backend Service:${NC}"
echo "   - In aaPanel, use 'Python Manager' to create a new project."
echo "   - Set 'Project path' to: ${PROJECT_PATH}/backend"
echo "   - Set 'Startup file' to: app.py"
echo "   - Set 'Port' to: 5001"
echo "   - Set 'Run as' to your user (e.g., www)."
echo "   - Submit to create and start the persistent Gunicorn service."

echo -e "\n${YELLOW}2. Configure Website Root:${NC}"
echo "   - In aaPanel -> Website, select your site (${DOMAIN_NAME})."
echo "   - Set the 'Website directory' to: ${PROJECT_PATH}/frontend/build"

echo -e "\n${YELLOW}3. Add Reverse Proxy:${NC}"
echo "   - Go to Website -> ${DOMAIN_NAME} -> Reverse proxy -> Config file."
echo "   - Paste the following configuration:"
echo -e "${GREEN}------------------------- START REVERSE PROXY -------------------------${NC}"
echo "$REVERSE_PROXY_CONFIG"
echo -e "${GREEN}-------------------------- END REVERSE PROXY --------------------------${NC}"

echo -e "\n${YELLOW}4. Add URL Rewrite Rules:${NC}"
echo "   - Go to Website -> ${DOMAIN_NAME} -> URL rewrite -> Config file."
echo "   - Paste the following configuration:"
echo -e "${GREEN}--------------------------- START URL REWRITE ---------------------------${NC}"
echo "$REWRITE_CONFIG"
echo -e "${GREEN}---------------------------- END URL REWRITE ----------------------------${NC}"

echo -e "\n${GREEN}Deployment helper finished!${NC}"
