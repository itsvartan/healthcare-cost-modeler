#!/bin/bash

echo "🏥 Hospital Cost Modeler - Quick Share"
echo "====================================="
echo ""
echo "Installing ngrok for temporary sharing..."

# Check if homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew first..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install ngrok
brew install ngrok/ngrok/ngrok 2>/dev/null || echo "ngrok already installed"

# Start Streamlit
echo "Starting your app..."
cd "$(dirname "$0")"
python3 -m streamlit run hospital_cost_model.py &
APP_PID=$!

# Wait for app to start
sleep 5

# Create public URL
echo ""
echo "Creating public URL..."
echo "====================================="
ngrok http 8501