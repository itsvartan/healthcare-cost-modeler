#!/bin/bash

echo "📤 GitHub Upload Helper"
echo "======================"
echo ""
echo "First, create a new repository on GitHub.com:"
echo "1. Go to https://github.com/new"
echo "2. Name it: healthcare-cost-modeler"
echo "3. Make it PUBLIC"
echo "4. DO NOT initialize with README"
echo "5. Click 'Create repository'"
echo ""
echo "Press Enter when you've created the repository..."
read

echo "What's your GitHub username?"
read GITHUB_USERNAME

echo ""
echo "Great! Now I'll set up your local repository..."
echo ""

cd "$(dirname "$0")"

# Initialize git
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Hospital construction cost modeling tool"

# Add remote (replace USERNAME with your actual username)
git remote add origin https://github.com/$GITHUB_USERNAME/healthcare-cost-modeler.git

# Push to GitHub
git branch -M main
git push -u origin main

echo ""
echo "✅ Done! Your code is now on GitHub!"
echo ""
echo "Next steps:"
echo "1. Go to https://share.streamlit.io"
echo "2. Click 'New app'"
echo "3. Select your repository: healthcare-cost-modeler"
echo "4. Main file: hospital_cost_model.py"
echo "5. Click Deploy!"