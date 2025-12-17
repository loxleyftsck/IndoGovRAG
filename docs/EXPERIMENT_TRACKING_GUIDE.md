# 🧪 Experiment Tracking Guide

**System:** Local JSON-based tracker (100% FREE, no account needed)  
**Alternative to:** Weights & Biases  
**Status:** ✅ Ready to use

---

## 🎯 Quick Start

### 1. Basic Usage

```python
from src.evaluation.experiment_tracker import (
    ExperimentTracker,
    create_experiment_config,
    ExperimentResult
)

# Initialize tracker
tracker = ExperimentTracker()

# Create experiment config
config = create_experiment_config(
    embedding_model="multilingual-e5-base",
    retrieval_strategy="vector",
    chunk_size=512,
    top_k=5,
    notes="Testing baseline RAG"
)

# Start experiment
exp_id = tracker.start_experiment(config, "Baseline Test")

# Log metrics during run
tracker.log_metrics({
    "hit_at_1": 0.80,
    "mrr": 0.85
}, step=1)

# Log messages
tracker.log("Completed evaluation on baseline dataset")

# Finish with final results
results = ExperimentResult(
    hit_at_1=0.80,
    hit_at_5=0.92,
    mrr=0.85,
    context_precision=0.87,
    context_recall=0.82,
    faithfulness=0.90,
    answer_relevancy=0.85,
    avg_latency_ms=120.0,
    p95_latency_ms=180.0,
    avg_cost_per_query=0.002,
    cache_hit_rate=0.0,
    total_queries=10,
    failed_queries=0,
    error_rate=0.0
)

tracker.finish_experiment(results)
```

---

## 📊 Features

### ✅ What It Tracks

**Configuration:**
- Embedding model
- LLM model
- Chunk size & overlap
- Retrieval strategy (vector/BM25/hybrid)
- Top-K and reranking settings
- Prompt template & generation params

**Metrics:**
- Hit@1, Hit@5, MRR (retrieval quality)
- Context precision & recall
- Faithfulness & answer relevancy
- Latency (avg, P95)
- Cost per query
- Cache hit rate
- Error rate

**System:**
- Experiment ID (auto-generated)
- Start/end timestamps
- Duration
- Logs and intermediate metrics

### ✅ Comparison

```python
# Compare multiple experiments
tracker.print_comparison([
    "exp_20241217_123456_abc123",
    "exp_20241217_124530_def456"
])
```

**Output:**
```
============================================================
📊 EXPERIMENT COMPARISON
============================================================

🔧 Configurations:
  Baseline Test (exp_20241217_123456_abc123):
    Embedding: multilingual-e5-base
    Retrieval: vector (top-k=5)
    Rerank: False
    Chunk size: 512

  Hybrid Test (exp_20241217_124530_def456):
    Embedding: multilingual-e5-base
    Retrieval: hybrid (top-k=5)
    Rerank: True
    Chunk size: 512

📈 Results:
Metric                   Baseline Test       Hybrid Test
------------------------------------------------------------
hit_at_1                 75.00%              ⭐ 85.00%
mrr                      0.820               ⭐ 0.890
faithfulness             88.00%              ⭐ 92.00%
answer_relevancy         83.00%              ⭐ 88.00%
avg_latency_ms           120.500             150.300
============================================================
```

---

## 📁 Data Storage

All experiments saved in `experiments/` directory:

```
experiments/
├── experiments_index.json          # Quick lookup
├── exp_20241217_123456_abc123.json # Full experiment data
└── exp_20241217_124530_def456.json
```

### Experiment File Format

```json
{
  "id": "exp_20241217_123456_abc123",
  "name": "Baseline Test",
  "project": "rag-indonesian-gov",
  "start_time": "2024-12-17T12:34:56",
  "end_time": "2024-12-17T12:35:30",
  "duration_seconds": 34.5,
  "config": {
    "embedding_model": "multilingual-e5-base",
    "retrieval_strategy": "vector",
    ...
  },
  "results": {
    "hit_at_1": 0.80,
    "mrr": 0.85,
    ...
  },
  "metrics_history": [
    {
      "timestamp": "2024-12-17T12:35:10",
      "step": 1,
      "metrics": {"hit_at_1": 0.80}
    }
  ],
  "logs": [
    {
      "timestamp": "2024-12-17T12:35:20",
      "level": "INFO",
      "message": "Completed evaluation"
    }
  ]
}
```

---

## 🔄 Week 3 Usage: A/B Testing

```python
# Test different chunk sizes
configs = [
    create_experiment_config(chunk_size=256, notes="Small chunks"),
    create_experiment_config(chunk_size=512, notes="Medium chunks"),
    create_experiment_config(chunk_size=1024, notes="Large chunks"),
]

experiment_ids = []

for config in configs:
    exp_id = tracker.start_experiment(config, f"Chunk Size {config.chunk_size}")
    
    # Run evaluation
    results = evaluate_rag_system(config)
    
    tracker.finish_experiment(results)
    experiment_ids.append(exp_id)

# Compare all
tracker.print_comparison(experiment_ids)
```

---

## 📈 List Recent Experiments

```python
# Get last 10 experiments
recent = tracker.list_experiments(limit=10)

for exp in recent:
    print(f"{exp['name']}: Hit@1={exp['key_metrics'].get('hit_at_1', 0):.2%}")
```

---

## 🎯 Integration with RAG Pipeline

```python
# In your evaluation script
from src.evaluation.experiment_tracker import ExperimentTracker

tracker = ExperimentTracker()

# Week 2: Baseline evaluation
config_baseline = create_experiment_config(
    embedding_model="multilingual-e5-base",
    retrieval_strategy="vector",
    chunk_size=512,
    top_k=5
)

exp_id = tracker.start_experiment(config_baseline, "Week 2 Baseline")

# Run RAGAS evaluation
from ragas import evaluate
ragas_results = evaluate(test_dataset, rag_pipeline)

# Convert to ExperimentResult
results = ExperimentResult(
    hit_at_1=ragas_results['context_recall'],  # Map appropriately
    # ... other metrics
)

tracker.finish_experiment(results)
```

---

## 🆚 Why Not W&B?

| Feature | This Tracker | Weights & Biases |
|---------|-------------|------------------|
| Cost | ✅ 100% FREE | Free tier limited |
| Account | ✅ Not needed | Requires signup |
| Offline | ✅ Works offline | Needs internet |
| Privacy | ✅ Local only | Data sent to cloud |
| Setup | ✅ Instant | Account + API key |
| Features | Basic (sufficient for MVP) | Advanced (charts, sweeps) |

**Decision:** Start with local tracker, migrate to W&B later if needed

---

## ✅ Week 0 Requirement Status

- [x] Experiment tracking system created
- [x] Metrics logging implemented
- [x] Comparison functionality working
- [x] JSON storage configured
- [x] No external dependencies
- [x] Demo tested successfully

**Status:** ✅ COMPLETE  
**Time:** 2 hours  
**Cost:** $0.00

---

## 🚀 Next Steps

### Week 2: First Usage
1. Track baseline RAG evaluation
2. Log RAGAS metrics
3. Compare against target thresholds

### Week 3: A/B Testing
1. Test chunk sizes (256, 512, 1024)
2. Compare retrieval strategies (vector, BM25, hybrid)
3. Test with/without reranking
4. Vary top-K (3, 5, 10)
5. Try different prompt templates

### Week 4: Production Monitoring
1. Track live system metrics
2. Monitor performance over time
3. Identify degradation early

---

**Created:** 2024-12-17  
**Ready for:** Week 2 evaluation experiments  
**Data stored:** `experiments/` directory (local)
