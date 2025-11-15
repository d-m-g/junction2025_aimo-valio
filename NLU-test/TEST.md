# Testing the NLU Parser API

## Quick Test Scripts

### Option 1: Python Test Script (Recommended)

Comprehensive test script with 10 prewritten test cases covering:
- Different intents (confirm, reject, report issue, etc.)
- Multiple languages (English, Finnish, Swedish)
- Various scenarios (vague text, specific requests, etc.)

**Usage:**
```bash
cd NLU
python test_api.py
```

**Requirements:**
```bash
pip install requests
```

The script will:
- Check if the API server is running
- Run all 10 test cases
- Display detailed results for each test
- Show a summary with pass/fail statistics
- Compare results against expected intents and sentiments

### Option 2: Simple Bash/Curl Script

Quick test using curl (no Python dependencies needed):

**Usage:**
```bash
cd NLU
./test_api_simple.sh
```

This runs 5 quick tests and displays JSON responses.

## Test Cases Included

1. **Confirm Substitution (English)** - "Yes, I'll accept the replacement milk"
2. **Confirm Substitution (Vague)** - "Yes, i agree on this"
3. **Reject Substitution** - "No thanks, I don't want a substitute"
4. **Request Callback** - "I need to speak to someone about my missing order"
5. **Report Issue** - "My delivery is missing 2 items - the milk and bread"
6. **Confirm Delivery** - "Received everything, all good! Thank you"
7. **Query Order Status** - "Where is my order? When will it arrive?"
8. **Provide Feedback** - "Great service! I'd like to leave some feedback"
9. **Finnish - Confirm Substitution** - "Kyllä, hyväksyn korvauksen"
10. **Swedish - Reject Substitution** - "Nej, jag vill inte ha ersättningen"

## Manual Testing

You can also test manually with curl:

```bash
curl -X POST http://localhost:5000/nlu/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Yes, I accept the replacement"}'
```

Or use the web interface at `NLU-test/index.html`

