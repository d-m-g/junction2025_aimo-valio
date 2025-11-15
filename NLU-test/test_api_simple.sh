#!/bin/bash

# Simple test script using curl
# Make sure the NLU API server is running first!

API_URL="http://localhost:5000/nlu/parse"

echo "🧪 Testing NLU Parser API"
echo "========================="
echo ""

# Test 1: Confirm substitution
echo "Test 1: Confirm Substitution"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Yes, I'\''ll accept the replacement milk"}' | python3 -m json.tool
echo ""
echo "---"
echo ""

# Test 2: Reject substitution
echo "Test 2: Reject Substitution"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "No thanks, I don'\''t want a substitute"}' | python3 -m json.tool
echo ""
echo "---"
echo ""

# Test 3: Report issue
echo "Test 3: Report Issue"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "My delivery is missing 2 items"}' | python3 -m json.tool
echo ""
echo "---"
echo ""

# Test 4: Request callback
echo "Test 4: Request Callback"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "I need to speak to someone about my order"}' | python3 -m json.tool
echo ""
echo "---"
echo ""

# Test 5: Finnish
echo "Test 5: Finnish - Confirm"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{"text": "Kyllä, hyväksyn korvauksen"}' | python3 -m json.tool
echo ""
echo "========================="
echo "Tests complete!"

