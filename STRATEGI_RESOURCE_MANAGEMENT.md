# 🔧 Strategi Resource Management: IndoGovRAG + Antigravity

**Tanggal:** 11 Januari 2026  
**Hardware Analysis:** Based on Task Manager Screenshots

---

## 📊 Hardware Inventory (Your System)

### Dari Screenshot Analysis

```yaml
CPU:
  Model: AMD Ryzen 7 7840HS
  Cores: 8 cores / 16 threads
  Base Clock: 3.8 GHz
  Boost Clock: ~4.0 GHz
  TDP: 35-54W
  Performance: ⭐⭐⭐⭐ Excellent (Zen 4)

Memory:
  Total RAM: 24 GB (23.2 GB available)
  Current Usage: 14.9 GB (65%)
  Available: 8.2 GB
  Speed: 5600 MT/s (DDR5)
  Type: SO-DIMM (laptop)
  
GPU:
  Model: NVIDIA GeForce RTX 3050 6GB (Laptop)
  VRAM: 6.0 GB dedicated
  Shared Memory: 11.6 GB (from system RAM)
  Architecture: Ampere (GA107)
  CUDA Cores: 2048
  Performance: ⭐⭐⭐ Good (entry-level)
  
iGPU:
  Model: AMD Radeon 780M (integrated)
  VRAM: Shared from system RAM
  Performance: ⭐⭐ Basic
  
Storage:
  Type: NVMe SSD
  Usage: Low (1-3%)
```

**Status Saat Ini (dari screenshot #3):**

- RAM Usage: 14.9 GB / 23.2 GB (65%)
- RAM Available: **8.2 GB** ⚠️
- Antigravity running: YES (consuming ~2-3 GB)
- IndoGovRAG API: YES (consuming ~1-2 GB)

---

## ⚠️ Problem Statement

**Challenge:**

1. ✅ 24 GB RAM cukup untuk Ollama 8B model (~8 GB)
2. ⚠️ **Concurrent usage:**
   - Antigravity: ~2-3 GB
   - IndoGovRAG API: ~1-2 GB
   - Ollama 8B: ~8 GB
   - **Total:** ~11-13 GB (saat semua aktif)
3. ⚠️ Current available: Only 8.2 GB
4. ❌ GPU VRAM: 6 GB insufficient untuk 8B model (needs 6-8 GB)

**Decision:** RAM atau GPU? 🤔

---

## 🆚 GPU vs CPU untuk Ollama: Deep Analysis

### Scenario 1: Run Ollama di GPU (RTX 3050 6GB)

**Pros:**

- ✅ **Much faster** inference (3-5x speedup)
- ✅ **Free up RAM** untuk Antigravity
- ✅ Parallel processing (CUDA cores)

**Cons:**

- ❌ **VRAM insufficient** untuk full 8B model
  - Llama 3.1 8B needs: **6-8 GB VRAM**
  - RTX 3050 has: **6 GB only**
  - Result: **Model won't fit** atau heavy swapping
- ❌ **Shared memory fallback** akan gunakan system RAM anyway
- ❌ **Thermal issues** (laptop GPU thermal throttling)
- ❌ Tidak bisa run Antigravity + GPU apps concurrently

**Verdict:** ⚠️ **MARGINAL** - GPU terlalu kecil untuk 8B model

---

### Scenario 2: Run Ollama di CPU (Ryzen 7 7840HS)

**Pros:**

- ✅ **Sufficient RAM** (24 GB total)
- ✅ **Ryzen 7 7840HS = powerful** (Zen 4, 8 cores)
- ✅ **No VRAM limit** - can run larger models
- ✅ More stable (no GPU thermal issues)
- ✅ **Better untuk laptop** (less heat, better battery)

**Cons:**

- ❌ **Slower** than GPU (3-5x slower)
  - GPU: ~45-60 tokens/sec
  - CPU: ~8-12 tokens/sec
- ❌ **Higher RAM usage** (~8 GB for model)
- ❌ CPU load ~50-80% during inference

**Verdict:** ✅ **RECOMMENDED** - More practical untuk current hardware

---

### Performance Comparison (RTX 3050 6GB vs Ryzen 7 7840HS)

| Metric | GPU (RTX 3050) | CPU (Ryzen 7) | Winner |
|--------|---------------|---------------|--------|
| **Tokens/sec (8B)** | 45-60 TPS* | 8-12 TPS | GPU |
| **Latency (avg query)** | ~3-5s* | ~8-12s | GPU |
| **VRAM requirement** | 6-8 GB | 0 GB | CPU |
| **RAM requirement** | 2-3 GB | 8-10 GB | GPU |
| **Thermal** | 70-85°C | 50-65°C | CPU |
| **Concurrent apps** | Limited | Good | CPU |
| **Stability** | Marginal | Stable | CPU |
| **8B model fit?** | ⚠️ Barely | ✅ Yes | CPU |

*Assuming model fits in VRAM (not guaranteed)

**Final Verdict:**  
🏆 **CPU (RAM-based) RECOMMENDED** untuk your hardware configuration

**Alasan:**

1. RTX 3050 6GB **too small** untuk comfortable 8B inference
2. Ryzen 7 7840HS **powerful enough** (Zen 4 = excellent single-thread)
3. 24GB RAM **sufficient** dengan proper management
4. **Better thermal** management pada laptop
5. **More headroom** untuk Antigravity concurrently

---

## 📊 Resource Allocation Strategy

### Optimal Configuration (24 GB RAM Total)

```yaml
# Resource Budget (Conservative)

System:
  Windows OS: 3-4 GB
  Background Apps: 2-3 GB
  Reserved: 1-2 GB
  Subtotal: 6-9 GB

IndoGovRAG (Ollama + API):
  Ollama 8B Model: 6-8 GB  # Using quantized version
  FastAPI Backend: 1-2 GB
  ChromaDB: 0.5-1 GB
  Semantic Cache: 0.5 GB
  Subtotal: 8-11.5 GB

Antigravity:
  Baseline: 2-3 GB
  Peak: 3-4 GB (during code generation)
  Target: 3 GB average

Total Used: 17-23.5 GB
Available Buffer: 0.5-7 GB ✅

# Safety Margin: ~ 3-5 GB
```

**Status:** ✅ **FEASIBLE** dengan optimizations

---

## 🎯 Optimization Strategy (3-Tier Approach)

### Tier 1: Model Quantization (Most Important)

**Current:** Llama 3.1 8B (full precision = 8 GB RAM)

**Options:**

| Quantization | Size | Quality Loss | RAM Savings | Recommended |
|--------------|------|--------------|-------------|-------------|
| **FP16 (full)** | 8 GB | 0% | Baseline | Current |
| **Q8** | 6 GB | <1% | **-25%** | ⭐ Recommended |
| **Q6_K** | 5 GB | <2% | **-37%** | Good option |
| **Q4_K_M** | 4 GB | 2-3% | **-50%** | Aggressive |
| **Q4_0** | 3.5 GB | 3-5% | **-56%** | Too lossy |

**Recommendation:** ⭐ **Q8 quantization** (6 GB, <1% quality loss)

```bash
# Download quantized model
ollama pull llama3.1:8b-q8_0

# For even more aggressive savings
ollama pull llama3.1:8b-q6_K  # 5 GB
```

**Impact:**

- RAM: 8 GB → 6 GB (**-2 GB saved**)
- Quality: <1% degradation (acceptable)
- Speed: Slightly faster (smaller model)

---

### Tier 2: Ollama Configuration Optimization

**Edit:** `~/.ollama/config.json` (or environment variables)

```json
{
  "num_parallel": 1,           // Only 1 concurrent request (save RAM)
  "num_gpu": 0,                // Force CPU mode
  "num_thread": 8,             // Use all 8 cores
  "num_ctx": 8192,             // Context window (reduce if needed)
  "mmap": true,                // Memory-map model (reduce RAM)
  "mlock": false,              // Don't lock model in RAM (allow swapping)
  "rope_frequency_base": 10000 
}
```

**Environment Variables:**

```bash
# Add to ~/.bashrc or startup script
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1  # Only keep 1 model loaded
export OLLAMA_HOST=0.0.0.0:11434
```

**Impact:**

- RAM: **-1-2 GB** (no parallel requests)
- Trade-off: Can't handle concurrent queries (acceptable untuk development)

---

### Tier 3: Antigravity Resource Limits

**Option A: Run Antigravity on Demand (Recommended)**

```bash
# Only run Antigravity when needed
# Close after task complete
# Frees ~3 GB RAM
```

**Option B: Limit Antigravity Memory (Advanced)**

```powershell
# Set process memory limit (Windows)
# This prevents Antigravity from consuming >4 GB
# Not officially supported, may cause issues
```

**Option C: Use Antigravity Web (Alternative)**

- Use Antigravity via web browser
- Runs on Google servers (no local RAM)
- Trade-off: Requires internet, less private

---

## 📋 Recommended Configurations

### Configuration 1: Development (Light Usage) ✅ **RECOMMENDED**

**Use Case:** Solo developer, occasional queries

```yaml
Ollama Model: llama3.1:8b-q8_0  # 6 GB
Ollama Config:
  num_parallel: 1
  num_ctx: 8192
  mmap: true
  
Antigravity: Run on-demand (close when not needed)

Total RAM: ~14-16 GB
Available: ~8-10 GB
Status: ✅ Comfortable
```

**Performance:**

- Latency: ~8-12s per query (acceptable)
- Concurrent: Antigravity OR Ollama (not both actively)

---

### Configuration 2: Production (Multi-User)

**Use Case:** Beta deployment, multiple concurrent users

```yaml
Ollama Model: llama3.1:8b-q6_K  # 5 GB (more aggressive)
Ollama Config:
  num_parallel: 2-3  # Allow some concurrency
  num_ctx: 4096      # Reduce context window
  mmap: true
  
Antigravity: Closed during production hours

Total RAM: ~12-14 GB
Available: ~10-12 GB
Status: ✅ Good
```

**Performance:**

- Latency: ~8-12s per query
- Concurrent: 2-3 users simultaneously

---

### Configuration 3: Aggressive Savings (Extreme)

**Use Case:** Limited RAM, want to run everything

```yaml
Ollama Model: llama3.1:8b-q4_K_M  # 4 GB
Alternative: qwen2.5:7b-q4_0       # 3.5 GB

Ollama Config:
  num_parallel: 1
  num_ctx: 4096
  mmap: true
  
Total RAM: ~10-12 GB
Available: ~12-14 GB
Status: ✅ Very comfortable (but quality trade-off)
```

**Trade-off:**

- RAM: Very low usage ✅
- Quality: -2-3% (noticeable degradation) ⚠️

---

## 🚀 Implementation Guide

### Step 1: Install Quantized Model

```bash
# Recommended: Q8 quantization (best quality/size ratio)
ollama pull llama3.1:8b-q8_0

# Alternative: Q6 (more aggressive)
ollama pull llama3.1:8b-q6_K

# Test the model
ollama run llama3.1:8b-q8_0 "Apa itu KTP elektronik?"
```

### Step 2: Update IndoGovRAG Configuration

```python
# Edit: src/rag/production_pipeline.py
# Line 36:

def __init__(
    self,
    ollama_model: str = "llama3.1:8b-q8_0",  # Changed to quantized
    ...
):
```

### Step 3: Configure Ollama Environment

```powershell
# Windows PowerShell
# Add to PowerShell profile or run before starting

$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"

# Start Ollama
ollama serve
```

### Step 4: Monitor Resource Usage

```bash
# During operation, monitor:
# - Task Manager (Memory tab)
# - Ollama logs: ollama ps
# - API response times

# Adjust config if needed
```

---

## 📊 Expected Performance

### Before Optimization

```yaml
RAM Usage:
  - Ollama 8B (FP16): 8 GB
  - API + Cache: 2 GB
  - Antigravity: 3 GB
  - System: 6 GB
  Total: 19 GB (81% of 24 GB) ⚠️

Available: 5 GB (tight)
Risk: OOM kills, swapping
```

### After Optimization (Config 1)

```yaml
RAM Usage:
  - Ollama 8B (Q8): 6 GB  (-2 GB ✅)
  - API + Cache: 1.5 GB (-0.5 GB ✅)
  - Antigravity: 0 GB (on-demand) (-3 GB ✅)
  - System: 6 GB
  Total: 13.5 GB (56% of 24 GB) ✅

Available: 10.5 GB (comfortable)
Risk: Low
```

**Savings:** **-5.5 GB** (29% reduction)

---

## 🔍 Monitoring & Troubleshooting

### Monitor RAM Usage

**Windows Task Manager:**

```
Ctrl + Shift + Esc
→ Performance tab
→ Memory

Watch for:
- Usage >90% (危险)
- Paging (swapping to disk = slow)
```

**Ollama Status:**

```bash
ollama ps  # Check loaded models
ollama list  # List available models
```

**Process-specific:**

```powershell
# PowerShell: Monitor specific process
Get-Process ollama, python | Select ProcessName, WorkingSet, PM

# Sort by memory
Get-Process | Sort-Object WS -Descending | Select -First 10
```

### Warning Signs

| Symptom | Cause | Solution |
|---------|-------|----------|
| **Slow responses (>30s)** | RAM swapping | Close Antigravity, reduce context |
| **OOM errors** | Exceeded RAM | Use smaller model (Q6/Q4) |
| **API crashes** | Memory leak | Restart API, check logs |
| **High disk activity** | Paging | Free up RAM immediately |

---

## 🎯 Final Recommendation Matrix

### Based on Your Hardware (24GB RAM, RTX 3050 6GB)

| Use Case | Model | Quantization | Concurrent Apps | RAM Usage | Performance |
|----------|-------|--------------|----------------|-----------|-------------|
| **Development** | Llama 3.1 8B | **Q8** | Antigravity on-demand | 14-16 GB | ⭐⭐⭐⭐ |
| **Production** | Llama 3.1 8B | **Q6_K** | No Antigravity | 12-14 GB | ⭐⭐⭐⭐ |
| **Extreme Savings** | Qwen 2.5 7B | **Q4_0** | Both concurrent | 10-12 GB | ⭐⭐⭐ |

**Recommended:** 🏆 **Configuration 1 (Development)**

- Model: `llama3.1:8b-q8_0`
- RAM: ~14-16 GB
- Antigravity: On-demand
- Performance: Excellent balance

---

## 📚 Referensi & Resources

**Ollama Optimization:**

- Ollama Docs: <https://ollama.com/docs>
- Quantization Guide: <https://ollama.com/blog/quantization>
- Performance Tuning: Community benchmarks

**Hardware-specific:**

- RTX 3050 6GB: Marginal untuk 8B models
- Ryzen 7 7840HS: Excellent CPU for LLM inference
- DDR5 5600: Fast enough untuk CPU inference

**Monitoring Tools:**

- Windows Task Manager (built-in)
- Process Explorer (Microsoft Sysinternals)
- GPU-Z (GPU monitoring)

---

## ✅ Quick Start Checklist

- [ ] Install quantized model: `ollama pull llama3.1:8b-q8_0`
- [ ] Update `production_pipeline.py` configuration
- [ ] Set environment: `OLLAMA_NUM_PARALLEL=1`
- [ ] Close Antigravity when running IndoGovRAG
- [ ] Monitor RAM usage in Task Manager
- [ ] Test performance: Run sample queries
- [ ] Adjust if needed (Q6 if still tight)

**Estimated Time:** 15 minutes  
**RAM Savings:** ~ 2-5 GB  
**Performance Impact:** <1% quality loss

---

**Disusun oleh:** IndoGovRAG Optimization Team  
**Berdasarkan:** Your hardware screenshots + industry benchmarks  
**Status:** ✅ **READY TO IMPLEMENT**
