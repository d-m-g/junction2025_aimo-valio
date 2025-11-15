# How to Run the NLU Parser

## Quick Start

### Option 1: Run API Server Only

```bash
cd NLU
pip install -r requirements.txt
python app.py
```

The API will be available at `http://localhost:5000`

### Option 2: Run API Server + Test Web Page

#### On macOS/Linux:

```bash
cd NLU-test
chmod +x run.sh
./run.sh
```

#### On Windows:

```bash
cd NLU-test
run.bat
```

#### Manual Method:

1. **Terminal 1 - Start API Server:**
   ```bash
   cd NLU
   pip install -r requirements.txt
   python app.py
   ```

2. **Terminal 2 - Open Test Page:**
   ```bash
   cd NLU-test
   # Open index.html in your browser
   # Or use a simple HTTP server:
   python -m http.server 8000
   # Then open http://localhost:8000 in browser
   ```

## Testing the API

### Using the Web Interface

1. Open `NLU-test/index.html` in your browser
2. Enter text in the input field
3. Click "Parse Text"
4. View results

### Using curl

```bash
curl -X POST http://localhost:5000/nlu/parse \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Yes, I accept the replacement",
    "session_id": "test-123"
  }'
```

### Using Python

```python
import requests

response = requests.post('http://localhost:5000/nlu/parse', json={
    'text': 'Yes, I accept the replacement',
    'session_id': 'test-123'
})

print(response.json())
```

## Health Check

Test if the server is running:

```bash
curl http://localhost:5000/health
```

## Troubleshooting

- **Port 5000 already in use**: Change the port in `app.py` (last line)
- **Module not found**: Run `pip install -r requirements.txt` in the NLU folder
- **CORS errors**: The web page should work fine, but if you need CORS, add Flask-CORS to requirements.txt

