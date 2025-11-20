#!/bin/bash

# Upwork Scraper Backend Runner

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Upwork Scraper Backend${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}⚠ .env file not found!${NC}"
    echo -e "${YELLOW}Copying .env.example to .env...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env with your configuration before running.${NC}"
    exit 1
fi

# Check MongoDB connection
echo -e "${YELLOW}Checking MongoDB connection...${NC}"
python -c "
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    print('✓ MongoDB connection successful')
except Exception as e:
    print(f'✗ MongoDB connection failed: {e}')
    exit(1)
" || exit 1

# Run the application
echo ""
echo -e "${GREEN}Starting server...${NC}"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
