#!/bin/bash

# Script to run both NLU API server and test web page

echo "🚀 Starting Valio Aimo NLU Test Environment"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask is not installed. Installing dependencies..."
    cd ../NLU
    pip3 install -r requirements.txt
    cd ../NLU-test
fi

echo "📦 Starting NLU API server..."
echo "   API will be available at: http://localhost:5000"
echo ""

# Start the Flask server in the background
cd ../NLU
python3 app.py &
FLASK_PID=$!

# Wait a moment for server to start
sleep 2

# Check if server started successfully
if ps -p $FLASK_PID > /dev/null; then
    echo "✅ NLU API server started (PID: $FLASK_PID)"
    echo ""
    echo "🌐 Opening test web page..."
    echo ""
    
    # Try to open the HTML file in the default browser
    # Go back to NLU-test directory
    cd "$(dirname "$0")"
    if command -v open &> /dev/null; then
        # macOS
        open index.html
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open index.html
    elif command -v start &> /dev/null; then
        # Windows
        start index.html
    else
        echo "📝 Please open NLU-test/index.html in your browser"
        echo "   Full path: $(pwd)/index.html"
    fi
    
    echo ""
    echo "✨ Test environment is ready!"
    echo ""
    echo "To stop the server, press Ctrl+C or run: kill $FLASK_PID"
    echo ""
    
    # Wait for user interrupt
    wait $FLASK_PID
else
    echo "❌ Failed to start NLU API server"
    exit 1
fi

