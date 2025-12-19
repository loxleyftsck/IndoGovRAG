# Week 3 Optimization - Quick Start Guide

**Goal:** Optimize RAG system through 5 systematic experiments

**Status:** Infrastructure ready, awaiting RAG pipeline integration

---

## ✅ What's Ready

### 1. Infrastructure
- ✅ A/B testing framework (`src/evaluation/ab_testing.py`)
- ✅ Experiment runner (`experiments/run_full_optimization.py`)
- ✅ Baseline evaluation script (`scripts/run_baseline_eval.py`)
- ✅ 50-question dataset (`data/eval_dataset_50q.json`)
- ✅ scipy installed for statistical tests

### 2. Experiment Plan
- Experiment 1: Retrieval Method (Vector vs BM25 vs Hybrid)
- Experiment 2: Chunk Size (256 vs 512 vs 1024)
- Experiment 3: Top-K (3 vs 5 vs 10)
- Experiment 4: Prompt Templates (3 variants)
- Experiment 5: Alpha Tuning (grid search)

---

## 🚧 What's Needed

### Integration Requirements

The framework is ready but needs integration with your RAG components:

#### 1. RAG Pipeline Wrapper
Create `src/rag/pipeline.py`:
```python
class RAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore()
        self.bm25 = BM25Search()
        self.llm = GeminiWrapper()
    
    def configure(self, config: ExperimentConfig):
        """Apply experiment configuration."""
        self.config = config
    
    def query(self, question: str, top_k: int = 5) -> Dict:
        """
        Run RAG query.
        
        Returns:
            {
                'answer': str,
                'contexts': List[str],
                'tokens_used': int,
                'metrics': {...}  # Optional RAGAS metrics
            }
        """
        # Retrieve documents
        if self.config.retrieval_method == 'vector':
            results = self.vector_store.search(question, top_k)
        elif self.config.retrieval_method == 'bm25':
            results = self.bm25.search(question, top_k)
        elif self.config.retrieval_method == 'hybrid':
            results = self.vector_store.hybrid_search(
                question, 
                top_k,
                alpha=self.config.alpha
            )
        
        contexts = [r.text for r in results]
        
        # Generate answer
        prompt = self._build_prompt(question, contexts)
        answer = self.llm.generate(prompt)
        
        return {
            'answer': answer,
            'contexts': contexts,
            'tokens_used': self.llm.last_token_count
        }
```

#### 2. Update Experiment Runner

In `experiments/run_full_optimization.py`:
```python
def setup_rag_pipeline(self):
    """Initialize RAG pipeline."""
    from src.rag.pipeline import RAGPipeline
    self.rag = RAGPipeline()
```

#### 3. API Key Configuration

Add to `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

---

## 🚀 Running Experiments

### Quick Test (5 questions)
```bash
# Test framework with small dataset
python experiments/run_full_optimization.py --limit 5
```

### Full Run (50 questions)
```bash
# 1. Run baseline first
python scripts/run_baseline_eval.py

# 2. Run all experiments (~2-3 hours)
python experiments/run_full_optimization.py

# Results will be in:
# - experiments/results/*.json
# - experiments/results/summary.json
```

---

## 📊 Expected Output

After experiments complete:

### Results Files
```
experiments/results/
  baseline_week3.json           # Baseline metrics
  retrieval_vector_only.json    # Exp 1
  retrieval_hybrid.json          # Exp 1
  chunk_256.json                 # Exp 2
  chunk_512.json                 # Exp 2  
  chunk_1024.json                # Exp 2
  topk_3.json                    # Exp 3
  topk_5.json                    # Exp 3
  topk_10.json                   # Exp 3
  prompt_concise.json            # Exp 4
  prompt_detailed.json           # Exp 4
  prompt_chain_of_thought.json   # Exp 4
  alpha_*.json                   # Exp 5 (7 files)
  summary.json                   # Consolidated
```

### Summary Structure
```json
{
  "experiments": [
    {
      "experiment": "retrieval_method",
      "winner": "hybrid",
      "comparison": {
        "metric_improvements": {
          "context_precision": 12.5,
          "hit_rate": 15.2
        },
        "p_values": {
          "context_precision": 0.023
        },
        "is_significant": {
          "context_precision": true
        }
      }
    }
  ],
  "winners": {
    "retrieval_method": "hybrid",
    "chunk_size": 512,
    "top_k": 5,
    "prompt_template": "detailed",
    "alpha": 0.5
  }
}
```

---

## 📋 Recommended Workflow

### Day 1: Setup & Testing
1. ✅ Review this guide
2. Create `src/rag/pipeline.py` wrapper
3. Test with 1-2 questions manually
4. Verify RAGAS metrics work
5. Run baseline eval (10 questions test)

### Day 2: Experiments 1-3
6. Run Experiment 1 (Retrieval Method)
7. Run Experiment 2 (Chunk Size)
8. Run Experiment 3 (Top-K)
9. Verify results are saving correctly

### Day 3: Experiments 4-5 & Analysis
10. Run Experiment 4 (Prompts)
11. Run Experiment 5 (Alpha Tuning)
12. Analyze summary.json
13. Document winners
14. Update `config/rag_config.yaml`

---

## 🎯 Success Criteria

- [ ] All 5 experiments completed on 50 questions
- [ ] Statistical significance proven (p<0.05)
- [ ] Min 5-10% improvement in key metrics
- [ ] Clear winner for each experiment
- [ ] Configuration updated with winners
- [ ] Results documented in `WEEK3_OPTIMIZATION_RESULTS.md`

---

## 🐛 Troubleshooting

### 413 Error: scipy not found
```bash
pip install scipy>=1.11.0
```

### RAG pipeline not configured
- Implement `src/rag/pipeline.py` wrapper
- See "Integration Requirements" section above

### RAGAS metrics are None  
- Check GEMINI_API_KEY is set in .env
- Verify RAGAS evaluator initialization
- Test with simple query first

### Experiments take too long
- Use `--limit 10` for quick testing
- Run experiments individually (modify runner)
- Check API quota and rate limits

---

## 📖 References

**Key Files:**
- [`src/evaluation/ab_testing.py`](file:///c:/Users/LENOVO/.gemini/antigravity/playground/magnetic-helix/src/evaluation/ab_testing.py) - Framework
- [`experiments/run_full_optimization.py`](file:///c:/Users/LENOVO/.gemini/antigravity/playground/magnetic-helix/experiments/run_full_optimization.py) - Runner
- [`data/eval_dataset_50q.json`](file:///c:/Users/LENOVO/.gemini/antigravity/playground/magnetic-helix/data/eval_dataset_50q.json) - Dataset

**Documentation:**
- `UPDATED_RAG_ROADMAP.md` - Week 3 objectives
- `implementation_plan.md` - Detailed plan
- `task.md` - Task checklist

---

**Last Updated:** 2024-12-19  
**Status:** Ready for RAG integration  
**Est. Time to Complete:** 3-4 hours (after integration)
