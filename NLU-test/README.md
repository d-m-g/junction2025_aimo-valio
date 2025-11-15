# NLU Test Web Interface

Simple web interface and test scripts for testing the Valio Aimo NLU Parser API.

## Quick Start

1. **Start the NLU API server** (in the `NLU` folder):
   ```bash
   cd NLU
   python app.py
   ```

2. **Run automated tests** (recommended):
   ```bash
   cd NLU-test
   python test_api.py
   ```
   This runs 10 prewritten test cases and shows detailed results.

3. **Or use the web interface**:
   - Simply open `index.html` in your web browser
   - Or use a local web server:
     ```bash
     # Python 3
     python -m http.server 8000
     
     # Then open http://localhost:8000 in your browser
     ```

## Test Scripts

### Python Test Script (`test_api.py`)

Comprehensive test suite with 10 prewritten test cases:
- Tests all major intents (confirm, reject, report issue, etc.)
- Multiple languages (English, Finnish, Swedish)
- Compares results against expected intents and sentiments
- Shows detailed pass/fail statistics

**Usage:**
```bash
cd NLU-test
python test_api.py
```

**Requirements:**
```bash
pip install requests
```

### Simple Bash Script (`test_api_simple.sh`)

Quick test using curl (5 test cases):

**Usage:**
```bash
cd NLU-test
./test_api_simple.sh
```

## Web Interface Features

- Clean, modern UI with gradient design
- Real-time API testing
- Visual confidence indicators
- Support for multiple languages
- Configurable API endpoint URL
- Full JSON response viewer
- Error handling and loading states

## Example Test Cases

- **English**: "Yes, I'll accept the replacement milk"
- **Finnish**: "Kyllä, hyväksyn korvauksen"
- **Swedish**: "Ja, jag accepterar ersättningen"
- **Issue Report**: "My delivery is missing 2 items"
- **Callback Request**: "I need to speak to someone about my order"

## Keyboard Shortcuts

- `Ctrl+Enter` (or `Cmd+Enter` on Mac): Submit the form

## Files

- `index.html` - Web interface for manual testing
- `test_api.py` - Python test script with 10 test cases
- `test_api_simple.sh` - Simple bash/curl test script
- `TEST.md` - Detailed testing documentation

