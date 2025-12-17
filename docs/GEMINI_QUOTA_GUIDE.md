# 🚀 Gemini Quota Tracker - Quick Start Guide

**100% FREE local quota tracking untuk Gemini API**

---

## 📦 Setup (2 menit)

### 1. Install Dependencies

```bash
pip install google-generativeai python-dotenv
```

### 2. Get Gemini API Key (Gratis!)

1. Buka: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy API key

### 3. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env dan paste API key
GEMINI_API_KEY=your-actual-key-here
```

---

## 🎯 Usage Examples

### Option 1: Quick Helper Functions (Termudah)

```python
from src.monitoring.gemini_quota_tracker import (
    track_gemini_request,
    print_quota_status,
    check_throttle
)

# Track request
result = track_gemini_request(
    input_tokens=500,
    output_tokens=200,
    query_preview="What is RAG?"
)

# Show status
print_quota_status()

# Check if should throttle
if check_throttle():
    print("⏸️ Rate limit reached, waiting...")
    time.sleep(60)
```

### Option 2: Full Client (Recommended)

```python
from src.monitoring.gemini_wrapper import GeminiClient
import os

# Initialize
client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))

# Single generation
result = client.generate(
    prompt="Explain RAG in 2 sentences",
    temperature=0.7,
    max_output_tokens=100
)

if result["success"]:
    print(result["response"])
    print(f"Tokens used: {result['quota']['this_request']['total_tokens']}")

# Check quota anytime
client.print_quota_status()
```

### Option 3: Batch Processing

```python
prompts = [
    "What is vector search?",
    "What is semantic chunking?",
    "What is RAGAS?",
]

results = client.generate_batch(
    prompts,
    delay_between_requests=0.5  # Respect rate limits
)

# Quota tracked automatically for all!
```

---

## 📊 Features

### ✅ Free Tier Limits Tracked

| Limit | Value | Auto-Tracked |
|-------|-------|--------------|
| Requests/minute | 15 RPM | ✅ |
| Tokens/minute | 1M TPM | ✅ |
| Requests/day | 1,500 RPD | ✅ |

### ✅ Alert Levels

- **WARNING (80%)**: Yellow alert, masih aman
- **CRITICAL (95%)**: Red alert, hampir limit

### ✅ Auto Features

- ✅ Local JSON storage (no external services)
- ✅ Automatic daily reset
- ✅ Rolling minute window tracking
- ✅ Retry logic on rate limits
- ✅ Batch processing with pacing
- ✅ Query history (last 100 calls)

---

## 🎨 Output Examples

### Status Display

```
============================================================
📊 GEMINI PRO QUOTA STATUS (FREE TIER)
============================================================
📅 Date: 2024-12-17

🗓️  DAILY USAGE:
   Requests: 234/1,500 (15.6%)
   Tokens:   45,678

⏱️  CURRENT MINUTE:
   Requests: 3/15 (20.0%)
   Tokens:   1,245/1,000,000 (0.1%)
============================================================
```

### Alerts

```
============================================================
⚠️  QUOTA ALERTS:
   ⚠️  WARNING: 1,200/1,500 daily requests used (80.0%)
   🚨 CRITICAL: 14/15 requests/min (93.3%)
============================================================
```

---

## 🧪 Testing

```bash
# Test quota tracker
python src/monitoring/gemini_quota_tracker.py

# Test full client (needs API key in .env)
python src/monitoring/gemini_wrapper.py
```

---

## 📁 Data Storage

Quota data disimpan di:
```
data/quota_tracking.json
```

Format:
```json
{
  "date": "2024-12-17",
  "daily_requests": 234,
  "daily_tokens": 45678,
  "minute_buckets": {
    "2024-12-17 10:30": {
      "requests": 3,
      "tokens": 1245
    }
  },
  "history": [
    {
      "timestamp": "2024-12-17T10:30:45",
      "model": "gemini-pro",
      "input_tokens": 500,
      "output_tokens": 200,
      "total_tokens": 700,
      "query_preview": "What is RAG?"
    }
  ]
}
```

---

## 🔧 Advanced: Custom Tracker

```python
from src.monitoring.gemini_quota_tracker import GeminiQuotaTracker

# Custom storage path
tracker = GeminiQuotaTracker(
    storage_path="custom/path/quota.json"
)

# Manual tracking
result = tracker.track_request(
    input_tokens=500,
    output_tokens=200,
    model="gemini-pro",
    query_preview="My query"
)

# Check throttle
should_throttle, reason = tracker.should_throttle()

# Get raw status
status = tracker.get_status()
print(status["daily"]["requests_percent"])
```

---

## 🚨 Troubleshooting

### "No module named 'google.generativeai'"

```bash
pip install google-generativeai
```

### "GEMINI_API_KEY not found"

1. Check `.env` file exists
2. Verify API key is set: `GEMINI_API_KEY=sk-...`
3. Load in code:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Rate Limit Hit

Client automatically retries with exponential backoff. Tapi kalau persistent:

```python
# Increase delay
client.generate(
    prompt="...",
    max_retries=5,
    retry_delay=120  # Wait 2 minutes
)
```

---

## 💰 Cost Tracking

Current implementation tracks tokens. Untuk cost estimation:

```python
# Gemini Pro pricing (per 1M tokens)
INPUT_COST = 0.00025  # $0.00025 per 1K input tokens
OUTPUT_COST = 0.0005  # $0.0005 per 1K output tokens

# Calculate cost
def estimate_cost(input_tokens, output_tokens):
    input_cost = (input_tokens / 1000) * INPUT_COST
    output_cost = (output_tokens / 1000) * OUTPUT_COST
    return input_cost + output_cost

# Example
cost = estimate_cost(500, 200)
print(f"Cost: ${cost:.6f}")  # ~$0.000225
```

---

## ✅ Week 0 Checklist

- [x] Token usage monitoring script
- [x] Daily quota tracking (1,500 RPD)
- [x] Alerts for 80% & 95% thresholds
- [x] Token counter for all API calls
- [x] Local JSON storage (no external deps)
- [x] Automatic retry logic
- [x] Batch processing support

**Status:** ✅ COMPLETE - 100% Gratis!

---

## 📚 Next Steps

1. **Test dengan real API key:**
   ```bash
   python src/monitoring/gemini_wrapper.py
   ```

2. **Integrate ke RAG pipeline** (Week 1):
   ```python
   from src.monitoring.gemini_wrapper import GeminiClient
   
   # In your RAG code
   llm_client = GeminiClient(api_key=GEMINI_API_KEY)
   
   # Generate with auto-tracking
   response = llm_client.generate(prompt=rag_prompt)
   ```

3. **Monitor daily usage** via dashboard (Week 4)

---

**Made with ❤️ for 100% FREE RAG system**
