#!/bin/bash

echo "Installing ngrok for quick sharing..."
brew install ngrok/ngrok/ngrok 2>/dev/null || echo "ngrok may already be installed"

echo "Starting the app..."
cd app && python app.py &
APP_PID=$!

sleep 3

echo "Creating public URL..."
ngrok http 8050