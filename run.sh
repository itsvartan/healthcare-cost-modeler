#!/bin/bash

# Healthcare Cost Modeler - Launch Script

echo "Starting Healthcare Architecture Cost Modeling Tool..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p exports
mkdir -p static/css
mkdir -p static/js

# Launch the application
echo "Launching application on http://localhost:8050"
cd app && python app.py