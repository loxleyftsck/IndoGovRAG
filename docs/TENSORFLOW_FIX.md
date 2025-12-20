# TensorFlow Fix Guide

**Issue:** TensorFlow bfloat16 conversion error  
**Python:** 3.11  
**TensorFlow:** 2.12.0  
**Sentence-Transformers:** 5.2.0

---

## The Problem

```
TypeError: Unable to convert function return value to a Python type! 
The signature was () -> handle
```

This is a known TensorFlow 2.12 + Python 3.11 compatibility issue on Windows.

---

## Solution Options

### Option 1: Downgrade Sentence-Transformers (FASTEST) ⚡

```bash
# Uninstall current version
pip uninstall sentence-transformers -y

# Install older compatible version
pip install sentence-transformers==2.2.2

# Test
python scripts/load_sample_docs.py
```

**Why:** Older sentence-transformers uses TensorFlow differently

---

### Option 2: Upgrade TensorFlow (RECOMMENDED) ✅

```bash
# Uninstall TensorFlow
pip uninstall tensorflow tensorflow-intel -y

# Install latest
pip install tensorflow==2.15.0

# OR CPU-only version (faster install)
pip install tensorflow-cpu==2.15.0

# Test
python scripts/load_sample_docs.py
```

**Why:** TensorFlow 2.15+ has better Python 3.11 support

---

### Option 3: Use PyTorch Backend (ALTERNATIVE) 🔄

```bash
# Uninstall TensorFlow
pip uninstall tensorflow tensorflow-intel -y

# sentence-transformers will use PyTorch instead
# (Already installed in requirements.txt)

# Test
python scripts/load_sample_docs.py
```

**Why:** sentence-transformers works with PyTorch too!

---

### Option 4: Downgrade Python to 3.10 (NUCLEAR) 💣

Only if above options fail. Not recommended.

---

## Quick Fix Script

```bash
# Try this first (fastest):
pip install sentence-transformers==2.2.2 --force-reinstall

# Then test:
python scripts/load_sample_docs.py
```

---

## Expected Output After Fix

```
🔧 Loading Sample Indonesian Government Documents...
📦 Initializing Vector Store...
✅ Vector store initialized
   Collection: indonesian_gov_docs
   Documents: 0
📝 Preparing 5 chunks...
💾 Adding to vector store...
  Progress: 100.0% (5/5)
✅ Added 5 chunks to vector store
✅ Successfully loaded 5 documents!
🔍 Testing search...
✅ Search working!
   Top result: Kartu Tanda Penduduk Elektronik (KTP-el) adalah kartu tanda penduduk yang dilengkapi dengan c...
🎉 Vector store ready with 5 documents!
```

---

## Verification

After fix, run:
```bash
python -c "from src.retrieval.vector_search import VectorStore; print('✅ OK')"
```

Should see: `✅ OK` (no errors)

---

**Recommended:** Try Option 1 first (fastest), then Option 3 if it fails.
