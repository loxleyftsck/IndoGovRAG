# 🔄 LLM Fallback Strategy

**Purpose:** Ensure RAG system continues working even when Gemini Pro hits quota limits  
**Status:** ✅ Implemented and documented

---

## 🎯 Fallback Tiers

### Tier 1: **Gemini Pro** (Primary)
- **Model:** `gemini-pro`
- **Free Tier:** 15 RPM, 1M TPM, 1.5K RPD
- **Quality:** Best
- **Use:** Default for all queries

### Tier 2: **Gemini Flash** (Fallback)
- **Model:** `gemini-1.5-flash`
- **Free Tier:** 15 RPM, 1M TPM, 1.5K RPD (separate quota!)
- **Quality:** Good (faster, slightly lower quality)
- **Use:** When Gemini Pro quota exceeded

### Tier 3: **Local Model** (Optional - Offline)
- **Model:** Llama 3 8B via Ollama
- **Free Tier:** Unlimited (runs locally)
- **Quality:** Acceptable (depends on model)
- **Use:** Complete fallback or offline mode

**Key Insight:** Gemini Pro and Gemini Flash have SEPARATE quotas!  
→ If Pro hits 1.5K daily limit, can still use Flask's 1.5K limit

---

## 🚀 Quick Start

### Basic Usage

```python
from src.llm.multi_tier_llm import MultiTierLLM

# Initialize with fallback enabled
llm = MultiTierLLM(
    gemini_api_key="your-key",
    enable_flash_fallback=True,  # Recommended!
    enable_local_fallback=False  # Optional
)

# Generate (automatic fallback)
response = llm.generate(
    prompt="Jelaskan RAG dalam 2 kalimat",
    temperature=0.7,
    max_output_tokens=100
)

if response.success:
    print(f"Response ({response.model_used}): {response.text}")
    print(f"Tokens: {response.tokens_used}, Latency: {response.latency_ms:.0f}ms")
else:
    print(f"Failed: {response.error}")

# View stats
llm.print_stats()
```

### Integration with Quota Tracker

```python
from src.monitoring.gemini_quota_tracker import GeminiQuotaTracker
from src.llm.multi_tier_llm import MultiTierLLM

# Initialize tracker
tracker = GeminiQuotaTracker()

# Initialize LLM with tracker
llm = MultiTierLLM(
    gemini_api_key=api_key,
    enable_flash_fallback=True,
    quota_tracker=tracker  # Automatic quota checking!
)

# Generate (quota checked before request)
response = llm.generate(prompt="...")
```

---

## 📊 Automatic Fallback Logic

```
1. Check Gemini Pro quota
   ├─ Quota OK? → Use Gemini Pro
   └─ Quota exceeded? → Try Gemini Flash

2. Try Gemini Flash
   ├─ Success? → Return response (fallback_triggered=True)
   └─ Failed? → Try local model (if enabled)

3. Try Local Model (optional)
   ├─ Available? → Use local model
   └─ Not available? → Return error
```

**Error Triggers:**
- "quota exceeded"
- "rate limit"
- 429 status code
- Any API timeout

**Non-Fallback Errors:**
- Invalid API key → Fail immediately
- Malformed prompt → Fail immediately
- Model initialization error → Fail immediately

---

## 📈 Statistics Tracking

The system tracks:
- **Total requests**
- **Gemini Pro success count**
- **Gemini Flash fallback count**
- **Local model fallback count**
- **Total failures**
- **Success rate**
- **Fallback rate**

```python
llm.print_stats()
```

**Output:**
```
============================================================
📊 LLM FALLBACK STATISTICS
============================================================
Total Requests:       25
Gemini Pro Success:   20 (80.0%)
Gemini Flash Fallback: 4 (16.0%)
Local Fallback:       0 (0.0%)
Total Failures:       1 (4.0%)

Success Rate:         96.0%
Fallback Rate:        16.0%
============================================================
```

---

## 🎯 When Fallback Triggers

### Scenario 1: Daily Quota Reached
```
User makes 1,500 requests to Gemini Pro
→ Request 1,501 quota error
→ Auto-switch to Gemini Flash
→ Flash has separate 1,500 quota!
→ Total: 3,000 requests/day possible
```

### Scenario 2: Rate Limit (RPM)
```
Burst of 20 requests in 1 minute
→ Requests 1-15 to Gemini Pro (success)
→ Request 16 rate limited
→ Auto-switch to Gemini Flash for request 16
→ Next minute: back to Gemini Pro
```

### Scenario 3: API Downtime
```
Gemini API temporarily down
→ All Pro requests fail
→ Auto-fallback to Flash
→ If Flash also down → Local model (if enabled)
```

---

## 🆚 Model Comparison

| Feature | Gemini Pro | Gemini Flash | Local Llama 3 |
|---------|-----------|--------------|---------------|
| **Quality** | Best | Good | Acceptable |
| **Speed** | ~120ms | ~60ms | ~500ms |
| **Cost** | Free (quota) | Free (quota) | Free (unlimited) |
| **Quota** | 1.5K RPD | 1.5K RPD | Unlimited |
| **Internet** | Required | Required | Not required |
| **Setup** | API key | API key | Local install |

**Recommendation:**
- **MVP:** Gemini Pro + Flash fallback ✅
- **Production:** Add local model for critical uptime
- **Offline:** Local model only

---

## 🛠️ Local Model Setup (Optional)

### Option 1: Ollama (Recommended)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Download Llama 3 8B
ollama pull llama3

# Test
ollama run llama3 "Jelaskan RAG"
```

**Integration:**
```python
def _try_local_model(self, prompt: str, **kwargs):
    """Use Ollama for local inference."""
    import requests
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )
    
    if response.status_code == 200:
        text = response.json()["response"]
        return LLMResponse(success=True, text=text, ...)
```

### Option 2: GPT4All

```bash
pip install gpt4all

python
>>> from gpt4all import GPT4All
>>> model = GPT4All("orca-mini-3b.gguf")
>>> model.generate("Explain RAG")
```

### Option 3: HuggingFace Transformers

```python
from transformers import AutoModelFor CausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat")
```

**Note:** Local models require:
- GPU (4GB+ VRAM) for decent speed
- Or CPU (slower, 8GB+ RAM)
- 4-8GB disk space per model

---

## ✅ Week 0 Testing Results

### Test Scenarios

**✅ Test 1: Normal Operation**
- Gemini Pro working → Uses Pro
- Result: Success ✅

**✅ Test 2: Quota Simulation**
- Manually trigger quota error → Falls back to Flash
- Result: Fallback working ✅

**✅ Test 3: Stats Tracking**
- Multiple requests → Stats accurate
- Result: Tracking working ✅

**⚠️ Test 4: Local Model**
- Not implemented yet (Week 1 optional)
- Result: Placeholder ready 🔧

---

## 📝 Integration Checklist

For Week 1 RAG implementation:

- [ ] Import `MultiTierLLM` instead of direct Gemini client
- [ ] Pass `quota_tracker` for automatic checking
- [ ] Enable Flash fallback (`enable_flash_fallback=True`)
- [ ] Log fallback events for monitoring
- [ ] Track fallback rate in experiment metrics

```python
# In RAG pipeline
from src.llm.multi_tier_llm import MultiTierLLM

llm = MultiTierLLM(
    gemini_api_key=GEMINI_API_KEY,
    enable_flash_fallback=True,
    quota_tracker=quota_tracker
)

def rag_query(user_query, context):
    prompt = f"Context: {context}\n\nQuestion: {user_query}\n\nAnswer:"
    
    response = llm.generate(prompt, temperature=0.7)
    
    if not response.success:
        logger.error(f"LLM failed: {response.error}")
        return "Sorry, I couldn't generate a response."
    
    if response.fallback_triggered:
        logger.warning(f"Fallback used: {response.model_used}")
    
    return response.text
```

---

## 🚨 Failure Handling

### What if all tiers fail?

```python
response = llm.generate(prompt)

if not response.success:
    # 1. Log error
    logger.error(f"All LLM tiers failed: {response.error}")
    
    # 2. Return cached response (if available)
    cached = get_cached_response(prompt_hash)
    if cached:
        return cached
    
    # 3. Return graceful error to user
    return {
        "answer": "I'm currently unable to generate a response. Please try again later.",
        "error": True,
        "fallback_exhausted": True
    }
```

---

## ✅ Week 0 Requirement Status

- [x] Gemini Flash fallback implemented
- [x] Automatic failover logic working
- [x] Quota integration tested
- [x] Statistics tracking added
- [x] Local model strategy documented
- [ ] Local model implementation (optional, defer to Week 1)

**Status:** ✅ COMPLETE  
**Confidence:** 95% - Flash fallback tested, local optional

---

## 📈 Expected Behavior in Production

**Typical Day (< quota limits):**
- 99% Gemini Pro
- 1% Gemini Flash (occasional rate limit bursts)
- 0% Local

**High Usage Day (approaching limits):**
- 50% Gemini Pro (until quota hit)
- 50% Gemini Flash (after Pro quota)
- 0% Local (unless both exhausted)

**Critical Scenario (both Gemini exhausted):**
- 0% Gemini Pro
- 0% Gemini Flash
- 100% Local (if enabled) OR graceful degradation

---

**Created:** 2024-12-17  
**Status:** ✅ Ready for Week 1 integration  
**Cost:** $0.00 (all free tiers)
