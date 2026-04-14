"""
Observability Configuration for IndoGovRAG
Customize these values for your production environment
"""

# === LATENCY SLO ===
# Based on user expectations for government document queries
LATENCY_SLO = {
    # Target percentiles (seconds)
    "target_p50": 5.0,       # 50th percentile: most queries <5s
    "target_p95": 30.0,      # 95th percentile: edge cases <30s  
    "target_p99": 60.0,      # 99th percentile: worst case <60s
    "critical_threshold": 120.0,  # Alert if ANY query >2 minutes
    
    # Per-stage budgets (milliseconds)
    "retrieval_budget_ms": 500,   # Vector search should be fast (<500ms)
    "llm_budget_ms": 30000,       # LLM generation is slow (Gemini free tier)
    "prompt_build_ms": 100        # Prompt construction overhead
}

# === ERROR RATE SLO ===
# Industry standard: 99% success rate (1% error acceptable)
ERROR_RATE_SLO = {
    "target": 0.01,         # 1% error rate target
    "warning": 0.05,        # 5% triggers warning alerts
    "critical": 0.10,       # 10% triggers critical alerts + possible rollback
    "measurement_window": "5m"  # Calculate over 5-minute rolling window
}

# === COST SLO ===
# Gemini Flash pricing: $0.00015 per 1K tokens (Jan 2026)
# Typical query: 1000 input + 200 output = 1200 tokens = $0.00018
COST_SLO = {
    # Per-query thresholds
    "target_per_query": 0.005,      # $0.005 normal (with re-ranking overhead)
    "warning_per_query": 0.05,      # $0.05 = 10x normal (investigate)
    "critical_per_query": 0.10,     # $0.10 = 20x normal (alert immediately)
    
    # Daily budgets
    "daily_budget_usd": 50.0,       # $50/day = ~10K queries at $0.005/query
    "daily_warning_usd": 40.0,      # Alert at 80% of daily budget
    
    # Monthly budgets
    "monthly_budget_usd": 1000.0,   # $1K/month
    "monthly_warning_usd": 800.0    # Alert at 80% of monthly budget
}

# === RAGAS QUALITY SLO ===
# Based on academic benchmarks and production systems
RAGAS_SLO = {
    "min_faithfulness": 0.70,       # Minimum acceptable (no hallucinations)
    "target_faithfulness": 0.85,    # Target score (excellent quality)
    
    "min_answer_relevancy": 0.75,   # Answer must address question
    "min_context_precision": 0.70,  # Retrieved docs must be relevant
    "min_context_recall": 0.80      # Must retrieve all needed info
}

# === SAFETY THRESHOLDS (for Week 2) ===
# Defined now for consistency
SAFETY_SLO = {
    # Toxicity detection (detoxify library)
    "max_toxicity_score": 0.7,      # Block content if toxicity >0.7
    "toxicity_categories": [
        "toxicity",
        "severe_toxicity",
        "obscene",
        "threat",
        "insult",
        "identity_attack"
    ],
    
    # Bias detection
    "max_bias_score": 0.6,          # Flag for review if bias >0.6
    
    # Evidence grounding
    "min_evidence_score": 0.5,      # Return "I don't know" if max retrieval score <0.5
    "min_evidence_count": 1         # Need at least 1 relevant doc
}

# === ALERT CONFIGURATION ===
ALERTS = {
    "enabled": True,
    
    # Destinations
    "log_file": "logs/alerts.log",
    "webhook_url": None,  # Set to Slack webhook: https://hooks.slack.com/...
    "email": None,        # Set to ops email: ops@yourdomain.com
    
    # Alert throttling (prevent spam)
    "cooldown_minutes": 15,         # Don't re-alert same issue for 15 minutes
    "max_alerts_per_hour": 10       # Max 10 alerts/hour to prevent noise
}

# === PROMETHEUS CONFIGURATION ===
PROMETHEUS = {
    "scrape_interval": "15s",       # Scrape metrics every 15 seconds
    "evaluation_interval": "15s",   # Evaluate rules every 15 seconds
    "retention": "15d",             # Keep metrics for 15 days
    
    # Metric bucket configurations
    "latency_buckets": [0.1, 0.5, 1, 5, 10, 30, 60, 120],  # seconds
    "cost_buckets": [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]    # USD
}

# === GRAFANA CONFIGURATION ===
GRAFANA = {
    "refresh_interval": "5s",       # Dashboard auto-refresh
    "default_time_range": "1h",     # Default view: last 1 hour
    
    # Panel-specific refresh rates
    "panel_refresh": {
        "realtime": "5s",    # QPS, current error rate (fast-changing)
        "medium": "30s",     # Latency percentiles (medium)
        "slow": "1m"         # Cost trends, RAGAS scores (slow-changing)
    }
}

# === TRACE CONFIGURATION ===
TRACING = {
    "enabled": True,
    "sample_rate": 1.0,             # Sample 100% of requests (change to 0.1 for high traffic)
    
    # Jaeger exporter
    "jaeger_host": "localhost",
    "jaeger_port": 6831,
    
    # Trace retention
    "retention_days": 7             # Keep traces for 7 days
}

# === DOMAINS & REGULATIONS (for governance) ===
# Customize based on your deployment region
GOVERNANCE = {
    "domain": "indonesian_government",
    "regulations": ["GDPR", "UU ITE"],  # Applicable regulations
    
    # Data retention (compliance)
    "log_retention_days": 90,       # Keep logs for 90 days
    "audit_retention_days": 365,    # Keep audit logs for 1 year
    
    # PII handling
    "anonymize_ip": True,           # Anonymize user IPs in logs
    "pii_detection_enabled": True   # Scan for PII in queries (Week 2)
}
