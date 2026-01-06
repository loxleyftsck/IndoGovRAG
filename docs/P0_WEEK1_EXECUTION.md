# 🚀 P0 Week 1 Execution Checklist

**Date:** 2026-01-07  
**Goal:** Activate drift monitoring + establish human review baseline  
**Time:** ~1.5 hours spread across 2 days

---

## ✅ Pre-Flight Check

### System Requirements

- [ ] Ollama running (`ollama list` shows llama3.1:8b)
- [ ] API functional (`python api/main.py` starts without errors)
- [ ] Prometheus installed (check `prometheus --version`)
- [ ] Production logs exist (`ls logs/ollama_queries_*.jsonl`)

### Files Exist

- [ ] `prometheus/alerts/quality_drift.yml`
- [ ] `scripts/extract_review_samples.py`
- [ ] `scripts/analyze_review_baseline.py`

---

## 1️⃣ Activate Prometheus Drift Alerts (15 min)

### Step 1.1: Update Prometheus Config

```bash
# Edit prometheus.yml
nano prometheus.yml  # or notepad prometheus.yml on Windows
```

Add to `rule_files` section:

```yaml
rule_files:
  - "alerts/indogovrag_alerts.yml"      # existing
  - "alerts/optimization_alerts.yml"    # existing
  - "alerts/quality_drift.yml"          # ← ADD THIS
```

### Step 1.2: Reload Prometheus

```bash
# If running via Docker
docker-compose restart prometheus

# OR if running standalone
curl -X POST http://localhost:9090/-/reload
```

### Step 1.3: Verify Alerts Active

```bash
# Check Prometheus UI
# Open: http://localhost:9090/alerts
# Should see 3 new rules:
#   - FaithfulnessDrift
#   - FaithfulnessBelowThreshold
#   - HallucinationRateSpike

# OR via command line
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="quality_monitoring") | .rules[].name'
```

**Expected Output:**

```
"FaithfulnessDrift"
"FaithfulnessBelowThreshold"
"HallucinationRateSpike"
```

✅ **Checkpoint:** Alerts visible in Prometheus UI

---

## 2️⃣ Extract Human Review Samples (10 min)

### Step 2.1: Run Extraction Script

```bash
python scripts/extract_review_samples.py
```

**Expected Output:**

```
🔍 Week 1 P0: Human Spot-Check Helper

📂 Loading production logs (past 7 days)...
   Found 42 queries

🎯 Selecting priority queries for review...
✅ Exported 10 queries to reports/human_review_batch.json

📋 Distribution:
   - Low faithfulness (<0.8): 2
   - Guardrail triggered: 3
   - High latency (>10s): 1
```

### Step 2.2: Verify Output File

```bash
cat reports/human_review_batch.json | jq '.total_samples'
# Should show: 10 (or close to it)
```

✅ **Checkpoint:** `reports/human_review_batch.json` created

---

## 3️⃣ Manual Review (30-45 min)

### Step 3.1: Open Review File

```bash
# Windows
notepad reports/human_review_batch.json

# Linux/Mac
code reports/human_review_batch.json  # or vim, nano
```

### Step 3.2: Fill in Review Fields

For EACH query in the file, add:

```json
{
  "id": 1,
  "query": "Apa itu KTP elektronik?",
  "answer": "KTP elektronik adalah...",
  "llm_judge_score": 0.85,
  
  // ← FILL THESE:
  "human_score": 0.90,              // Your faithfulness rating (0.0-1.0)
  "human_is_hallucination": false,  // true if answer contains false info
  "review_notes": "Answer accurate, judge slightly under-scored due to brevity",
  "edge_cases_identified": []       // e.g., ["missing_legal_citation"]
}
```

**Rating Guide:**

- **1.0:** Perfect, fully faithful to context
- **0.8-0.9:** Mostly faithful, minor omissions
- **0.6-0.7:** Partially faithful, some unsupported claims
- **<0.6:** Significant issues or hallucination

**Common Edge Cases:**

- `missing_temporal_info` - Answer doesn't include timeframes
- `missing_legal_citation` - No pasal/UU reference
- `out_of_scope_not_detected` - Guardrail should have triggered
- `hallucination_judge_missed` - Judge gave high score despite hallucination
- `over_clarification` - Guardrail was too aggressive

### Step 3.3: Save Completed Review

```bash
# Save as:
reports/human_review_batch_20260107_COMPLETED.json
```

✅ **Checkpoint:** All 10 queries reviewed and saved

---

## 4️⃣ Compile Baseline (10 min)

### Step 4.1: Run Analyzer

```bash
python scripts/analyze_review_baseline.py
```

**Expected Output:**

```
📊 WEEK 1 BASELINE ANALYSIS
=========================================

✅ Analyzed 10 human-reviewed queries

📈 SUMMARY STATISTICS:
   Human Avg Faithfulness:  0.84
   LLM Avg Faithfulness:    0.82
   Judge-Human Correlation: 0.91 (Excellent)
   ✅ Judge alignment is acceptable (>0.70)

🔍 DISCREPANCIES:
   High Discrepancy Rate: 0.20 (2/10 queries)

🚨 EDGE CASES IDENTIFIED:
   - missing_temporal_info: 2 occurrences
   - out_of_scope_not_detected: 1 occurrence

💡 RECOMMENDATIONS (2 items):
   [P1] GUARDRAIL_GAP
   Finding: Temporal info missing in 2 queries
   Action:  Add guardrail pattern: check if query asks 'berapa lama'

📁 Full report saved to: reports/human_review_baseline_week1.json
```

### Step 4.2: Review Baseline Report

```bash
cat reports/human_review_baseline_week1.json | jq '.summary_statistics'
```

✅ **Checkpoint:** Baseline report generated

---

## 📊 Success Criteria Check

After completing all steps, verify:

| Criterion | Target | Check |
|-----------|--------|-------|
| Prometheus alerts active | 3 rules | [ ] |
| Human reviews completed | 5-10 queries | [ ] |
| Judge-Human correlation | >0.70 | [ ] |
| Edge cases documented | ≥1 identified | [ ] |
| Baseline report saved | JSON file exists | [ ] |

---

## 🚨 Troubleshooting

### Issue: No production logs found

```bash
# Check if API has been running
ls -la logs/

# If empty, run some test queries first
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Apa itu KTP elektronik?"}'
```

### Issue: Prometheus not loading rules

```bash
# Check Prometheus logs
docker logs indogovrag_prometheus | tail -20

# Common issue: YAML syntax error
yamllint prometheus/alerts/quality_drift.yml
```

### Issue: Correlation too low (<0.70)

**Possible causes:**

- LLM judge prompt needs tuning
- Human reviewers not calibrated (review guidelines together)
- Sample too small (review 15 queries instead of 10)

**Action:** Document in baseline report, continue monitoring in Week 2.

---

## 📅 Timeline

| Day | Task | Duration |
|-----|------|----------|
| **Today (Tue)** | 1️⃣ Prometheus alerts | 15 min |
| **Today (Tue)** | 2️⃣ Extract samples | 10 min |
| **Today-Wed** | 3️⃣ Manual review | 30-45 min |
| **Wed-Fri** | 4️⃣ Compile baseline | 10 min |

**Total:** ~1.5 hours over 2-3 days

---

## ✅ Completion Checklist

- [ ] Prometheus alerts deployed and firing (or in "pending" state)
- [ ] Human review batch extracted and saved
- [ ] All queries manually reviewed with scores
- [ ] Baseline report generated
- [ ] Recommendations reviewed and noted for Week 2
- [ ] Baseline committed to git

```bash
# Final commit
git add reports/ prometheus/alerts/ scripts/
git commit -m "feat(p0): Week 1 baseline complete

- Activated Prometheus drift alerts
- Completed 10 human reviews
- Judge-human correlation: [X.XX]
- Edge cases identified: [N]
- Ready for P1 (Week 2)"
```

---

## 🚀 Next: Week 2 P1 Items

After P0 is stable:

1. **Retrieval Metrics:** Context precision/recall
2. **User Feedback API:** Thumbs up/down endpoint
3. **Guardrail Tuning:** Based on Week 1 edge cases

**Status:** P0 execution in progress! 🎯
