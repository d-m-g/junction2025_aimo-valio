# Quick Start Guide

## One-Time Setup

### macOS / Linux
```bash
./setup.sh
```

### Windows
```cmd
setup.bat
```

This will:
- ✅ Create a Python virtual environment
- ✅ Install all dependencies
- ✅ Prepare everything for running

## Running the Server

### macOS / Linux
```bash
./run.sh
```

### Windows
```cmd
run.bat
```

The server will start at: **http://localhost:5000**

## Test It

Once the server is running, test it with:

```bash
curl -X POST http://localhost:5000/nlu/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Yes, I accept the replacement milk"}'
```

Or check health:
```bash
curl http://localhost:5000/health
```

## Troubleshooting

**Port already in use?**
- On macOS, disable AirPlay Receiver: System Preferences → General → AirDrop & Handoff
- Or change the port in `config.py` or set `NLU_API_PORT=5001`

**Virtual environment not found?**
- Run `./setup.sh` (or `setup.bat` on Windows) first

**Dependencies not installing?**
- Make sure you have Python 3.8 or higher: `python3 --version`
- Try upgrading pip: `pip install --upgrade pip`

## Next Steps

- See `README.md` for full API documentation
- Check `NLU-test/` folder for a web-based test interface
- Review `CHANGELOG.md` for recent updates

