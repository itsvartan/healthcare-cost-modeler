#!/bin/bash

echo "🏥 Starting Healthcare Cost Modeler..."
echo "=================================="

cd "$(dirname "$0")"

echo "📦 Installing required packages..."
pip3 install streamlit plotly pandas --quiet

echo "🚀 Launching the app..."
echo "=================================="
echo "✅ Your browser should open automatically"
echo "✅ If not, go to: http://localhost:8501"
echo "=================================="
echo "Press Ctrl+C to stop the app"
echo ""

streamlit run streamlit_app.py