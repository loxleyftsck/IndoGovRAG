# Continuous Improvement Workflow

## Feedback Loop for RAG Quality

---

## 🔄 WEEKLY IMPROVEMENT CYCLE

### **Monday: Collect & Analyze**

**Step 1: Pull Feedback Data**

```bash
python scripts/review_feedback.py
```

**Output:**

- Total feedback count
- Average rating
- Low-rated queries (<3 stars)
- Common issues/themes

**Step 2: Categorize Issues**

| Category | Description | Example |
|----------|-------------|---------|
| **Retrieval** | Wrong documents retrieved | Query about "KTP" returns "paspor" docs |
| **Generation** | Answer inaccurate/incomplete | Missing key requirements |
| **Coverage** | Topic not in knowledge base | Query about "SIM internasional" (no docs) |
| **Safety** | False positives | Good content filtered as toxic |

---

### **Tuesday: Investigate Root Causes**

**For each low-rated query:**

1. **Check Retrieval Quality**

   ```python
   # Get retrieval scores from audit log
   audit_entry = audit_logger.query_by_request_id(request_id)
   scores = audit_entry['retrieval_scores']
   
   if max(scores) < 0.5:
       print("❌ Low retrieval scores - Need better docs")
   ```

2. **Check Answer Accuracy**
   - Compare answer to source documents
   - Verify no hallucinations
   - Check if answer addresses question

3. **Identify Pattern**
   - Is this a one-off issue or systemic?
   - Multiple similar queries failing?

---

### **Wednesday: Implement Improvements**

**For Retrieval Issues:**

- Add query to golden test set
- Adjust retrieval parameters (alpha, top_k)
- Add missing documents

**For Generation Issues:**

- Update prompt template
- Add few-shot examples
- Adjust temperature/max_tokens

**For Coverage Gaps:**

- Identify missing document topics
- Add to data collection backlog
- Document in coverage analysis

**For Safety Issues:**

- Adjust toxicity threshold
- Update evidence grounding min_score
- Add edge cases to test set

---

### **Thursday: Validate Changes**

**Step 1: Run RAGAS on Golden Set**

```bash
python scripts/evaluate_ragas.py --golden-set data/golden_set_v3.json
```

**Target Metrics:**

- Faithfulness: ≥0.85
- Answer Relevancy: ≥0.80
- Context Precision: ≥0.75

**Step 2: Test Affected Queries**

```python
# Re-run low-rated queries
for query in low_rated_queries:
    result = rag_pipeline.query(query)
    # Verify improvement
```

**Step 3: Smoke Test**

- Run top 20 common queries
- Verify no regressions

---

### **Friday: Deploy & Monitor**

**Step 1: Canary Deployment**

```bash
# Deploy with changes
flyctl deploy --strategy canary --app indogovrag-staging

# Monitor for 1 hour
python scripts/post_deploy_check.py
```

**Step 2: Monitor Feedback**

- Watch for new feedback
- Check if rating improves
- Monitor error rates

**Step 3: Document Changes**

```markdown
# Update CHANGELOG.md
## 2026-01-17
- Improved retrieval for KTP queries (alpha: 0.5 → 0.6)
- Added 3 documents on "SIM internasional"
- Updated golden set (v2 → v3, +5 queries)
- RAGAS faithfulness: 0.82 → 0.87
```

---

## 📊 MONTHLY REVIEW

### **First Monday of Month**

**Aggregate Metrics:**

- Total queries this month
- Average rating trend
- RAGAS score trend
- Top improvement areas

**Model Updates:**

- Consider embedding model upgrade
- Evaluate newer LLM versions
- Review prompt template effectiveness

**Coverage Analysis:**

- Which topics have most queries?
- Which topics have fewest documents?
- Prioritize data collection

---

## 🎯 GOLDEN SET UPDATE PROCESS

### **Adding to Golden Set**

**Criteria for Inclusion:**

1. Real user query (from feedback)
2. Representative of common use case
3. Has known correct answer
4. Diverse (not duplicate of existing)

**Format:**

```json
{
  "question": "User's exact question",
  "ground_truth_answer": "Correct answer (verified)",
  "context": ["Relevant document IDs"],
  "metadata": {
    "category": "KTP",
    "difficulty": "medium",
    "added_date": "2026-01-11",
    "source": "user_feedback_request_xyz"
  }
}
```

**Version Control:**

```bash
# Golden set is versioned
data/golden_set_v1.json  # Baseline (20 queries)
data/golden_set_v2.json  # Week 1 update (+10 queries)
data/golden_set_v3.json  # Week 2 update (+5 queries)
```

---

## 🚨 EMERGENCY RESPONSE

### **If Rating Drops Significantly**

**Trigger:** Average rating drops from 4.2 to <3.5 in 24 hours

**Immediate Actions:**

1. Check recent deployments (rollback if needed)
2. Review last 50 queries for patterns
3. Check for system errors/outages
4. Alert team

**Investigation:**

```bash
# Quick diagnosis
python scripts/diagnose_rating_drop.py --last-hours 24
```

**Recovery:**

- Rollback if deployment caused issue
- Hot-fix if bug identified
- Communication to users if needed

---

## 📈 SUCCESS METRICS

**Weekly:**

- Average rating ≥4.0
- Low-rated queries <10%
- RAGAS faithfulness ≥0.85

**Monthly:**

- Rating trend: stable or improving
- Coverage gaps: decreasing
- Response time: <10s (P95)

---

## 🔧 TOOLS & SCRIPTS

**Required Scripts:**

- `scripts/review_feedback.py` - Analyze feedback
- `scripts/evaluate_ragas.py` - Run RAGAS
- `scripts/update_golden_set.py` - Add to golden set
- `scripts/post_deploy_check.py` - Validate deployment

**Dashboards:**

- Grafana: Real-time metrics
- Feedback Review: Weekly analysis
- RAGAS Trends: Quality over time

---

**Owner:** Data/ML Team  
**Frequency:** Weekly (core cycle) + Monthly (deep review)  
**Tools:** Python scripts + Grafana + Golden set versioning
