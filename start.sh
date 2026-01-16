#!/bin/bash

# HKPC PPE Detection System - Startup Script

echo "================================================"
echo "HKPC PPE Detection Access Control System"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Check if YOLO model exists
if [ ! -f "yolo10s.pt" ]; then
    echo "WARNING: yolo10s.pt not found!"
    echo "Please ensure the YOLO model file is in the project directory."
    exit 1
fi

echo ""
echo "================================================"
echo "Starting HKPC PPE Detection System..."
echo "================================================"
echo ""
echo "Main Interface: http://localhost:5000/"
echo "Admin Panel:    http://localhost:5000/admin"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"
echo ""

# Run the application
python app.py



