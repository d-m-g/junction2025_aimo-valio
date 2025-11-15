#!/bin/bash
# Run script for NLU Parser API
# Activates virtual environment and starts the Flask server

set -e  # Exit on error

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    pip install -r requirements.txt
fi

# Start the server
echo ""
echo "🚀 Starting NLU Parser API server..."
echo "   Server will be available at: http://localhost:5000"
echo "   Health check: http://localhost:5000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py

