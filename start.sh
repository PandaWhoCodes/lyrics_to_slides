#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Lyrics to Slides App...${NC}\n"

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip install -q -r requirements.txt

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${GREEN}Installing Node dependencies...${NC}"
    npm install
fi

# Start backend in background
echo -e "${GREEN}Starting backend server on port 8000...${NC}"
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}Starting frontend on port 5173...${NC}"
npm run dev &
FRONTEND_PID=$!

echo -e "\n${BLUE}================================${NC}"
echo -e "${GREEN}App is running!${NC}"
echo -e "${BLUE}Frontend: http://localhost:5173${NC}"
echo -e "${BLUE}Backend: http://localhost:8000${NC}"
echo -e "${BLUE}================================${NC}\n"
echo -e "Press Ctrl+C to stop the servers\n"

# Trap Ctrl+C to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait for both processes
wait
