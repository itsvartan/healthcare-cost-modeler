#!/bin/bash

echo "🚀 Hospital Cost Modeler - Quick Deploy"
echo "======================================"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git..."
    git init
    git remote add origin https://github.com/itsvartan/healthcare-cost-modeler.git
fi

# Add all changes
echo "📦 Preparing changes..."
git add .

# Commit with timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
echo "💾 Saving changes..."
git commit -m "Update: $TIMESTAMP"

# Push to GitHub
echo "📤 Uploading to GitHub..."
git push origin main

echo ""
echo "✅ Done! Your app will update in 1-2 minutes"
echo "🌐 View at: https://share.streamlit.io"
echo ""
echo "Press any key to close..."
read -n 1