# Windows Compatibility Fix

## Issue
On Windows systems, aiodns library requires a SelectorEventLoop but Windows defaults to ProactorEventLoop in Python 3.8+. This causes the error:

```
aiodns needs a SelectorEventLoop on Windows. See more: https://github.com/saghul/aiodns/issues/86
```

## Solution Applied

### 1. Event Loop Policy Fix (in unified_server.py)
Added Windows-specific event loop policy configuration:

```python
# Fix Windows event loop policy for aiodns compatibility
if platform.system() == 'Windows':
    try:
        import asyncio
        if sys.version_info >= (3, 8):
            # Windows ProactorEventLoop doesn't support aiodns
            # Force SelectorEventLoop on Windows
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logging.info("Set Windows SelectorEventLoop policy for aiodns compatibility")
    except Exception as e:
        logging.warning(f"Failed to set Windows event loop policy: {e}")
```

### 2. Alternative Solutions (if above doesn't work)

#### Option A: Install windows-specific packages
```bash
pip install aiodns==3.0.0
pip install pycares
```

#### Option B: Use pure HTTP fallback
The system automatically falls back to basic HTTP extraction when aiodns fails.

#### Option C: Set environment variable
```bash
set PYTHONUNBUFFERED=1
```

### 3. Testing on Windows
1. Start the server: `python unified_server.py`
2. Test with: `curl -X POST http://localhost:5000/api/extract -H "Content-Type: application/json" -d '{"url": "https://example.com"}'`

## Status
✅ Windows compatibility fix implemented in unified_server.py
✅ Automatic fallback to HTTP extraction if aiodns fails
✅ Logging added to track Windows event loop policy changes