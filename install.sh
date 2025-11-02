#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Lyrics to Slides - Ubuntu Installer  ${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if running on Ubuntu/Debian
if [ ! -f /etc/debian_version ]; then
    echo -e "${YELLOW}Warning: This installer is designed for Ubuntu/Debian systems.${NC}"
    echo -e "${YELLOW}You may need to adapt it for your distribution.${NC}\n"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update package list
echo -e "${GREEN}Updating package list...${NC}"
sudo apt update

# Install Python 3 and pip if not installed
if ! command_exists python3; then
    echo -e "${GREEN}Installing Python 3...${NC}"
    sudo apt install -y python3
else
    echo -e "${BLUE}Python 3 already installed: $(python3 --version)${NC}"
fi

if ! command_exists pip3; then
    echo -e "${GREEN}Installing pip3...${NC}"
    sudo apt install -y python3-pip
else
    echo -e "${BLUE}pip3 already installed${NC}"
fi

# Install python3-venv for virtual environment
echo -e "${GREEN}Installing python3-venv...${NC}"
sudo apt install -y python3-venv

# Install Node.js and npm if not installed
if ! command_exists node; then
    echo -e "${GREEN}Installing Node.js and npm...${NC}"
    # Install Node.js 18.x LTS
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
else
    echo -e "${BLUE}Node.js already installed: $(node --version)${NC}"
    echo -e "${BLUE}npm already installed: $(npm --version)${NC}"
fi

# Install system dependencies for Playwright
echo -e "${GREEN}Installing system dependencies for Playwright...${NC}"
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0

# Create Python virtual environment
echo -e "\n${GREEN}Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists, skipping...${NC}"
else
    python3 -m venv venv
fi

# Activate virtual environment and install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo -e "${GREEN}Installing Playwright Chromium browser...${NC}"
playwright install chromium
playwright install-deps chromium

# Install Node.js dependencies
echo -e "${GREEN}Installing Node.js dependencies...${NC}"
npm install

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  WARNING: .env file not found!${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Please create a .env file with the following keys:${NC}\n"
    echo -e "XAI_API_KEY=your_xai_api_key_here"
    echo -e "GOOGLE_API_KEY=your_google_api_key_here"
    echo -e "GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here\n"
    echo -e "${YELLOW}You can copy .env.example if it exists.${NC}\n"
else
    echo -e "${GREEN}.env file found!${NC}"
fi

# Make start.sh executable
if [ -f "start.sh" ]; then
    chmod +x start.sh
    echo -e "${GREEN}Made start.sh executable${NC}"
fi

# Deactivate virtual environment
deactivate

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"
echo -e "${GREEN}To start the application, run:${NC}"
echo -e "${BLUE}  ./start.sh${NC}\n"
echo -e "${GREEN}The app will be available at:${NC}"
echo -e "${BLUE}  Frontend: http://localhost:5173${NC}"
echo -e "${BLUE}  Backend: http://localhost:8000${NC}\n"

if [ ! -f ".env" ]; then
    echo -e "${RED}IMPORTANT: Don't forget to create your .env file!${NC}\n"
fi
