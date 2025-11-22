#!/bin/bash
# Quick test script for WebSocket setup
# Run: bash test_setup.sh

echo "=========================================="
echo "Testing Transcript WebSocket Setup"
echo "=========================================="
echo ""

# Check if websockets is installed
echo "1. Checking dependencies..."
python3 -c "import websockets" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ websockets is installed"
else
    echo "   ❌ websockets is NOT installed"
    echo "   Install it with: pip install websockets"
    exit 1
fi

echo ""
echo "2. Starting server..."
echo "   Run this in Terminal 1:"
echo "   python transcript_server.py --port 8765 --model base"
echo ""
echo "3. Testing connection..."
echo "   Run this in Terminal 2:"
echo "   python test_transcript_client.py --port 8765"
echo ""
echo "4. If connected successfully, speak into your microphone"
echo "   and transcripts should appear in Terminal 2!"
echo ""
echo "=========================================="



