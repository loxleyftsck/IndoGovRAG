"""
Prometheus Metrics for IndoGovRAG
Production-ready metrics instrumentation

Metrics Types:
- Counter: Monotonically increasing (total queries)
- Histogram: Distribution (latency, cost)
- Gauge: Current value (RAGAS score)

Best Practice: https://prometheus.io/docs/practices/naming/
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# === REQUEST METRICS ===

# Total queries counter
queries_total = Counter(
    name='indogovrag_queries_total',
    documentation='Total number of RAG queries processed',
    labelnames=['status', 'model', 'endpoint']
)

# Query latency histogram
query_latency_seconds = Histogram(
    name='indogovrag_query_latency_seconds',
    documentation='End-to-end query latency in seconds',
    labelnames=['endpoint'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 120]  # From config
)

# === COMPONENT METRICS ===

# Retrieval latency
retrieval_latency_seconds = Histogram(
    name='indogovrag_retrieval_latency_seconds',
    documentation='Document retrieval latency',
    labelnames=['method'],  # vector, hybrid, bm25
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

# LLM generation latency
llm_latency_seconds = Histogram(
    name='indogovrag_llm_latency_seconds',
    documentation='LLM generation latency',
    labelnames=['model'],
    buckets=[1, 5, 10, 30, 60, 120]
)

# Compression latency (BET-007)
compression_latency_seconds = Histogram(
    name='indogovrag_compression_latency_seconds',
    documentation='Context compression latency',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

# Cache lookup latency (BET-007)
cache_latency_seconds = Histogram(
    name='indogovrag_cache_latency_seconds',
    documentation='Cache lookup latency',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

# === QUALITY METRICS ===

# Query cost
query_cost_usd = Histogram(
    name='indogovrag_query_cost_usd',
    documentation='Cost per query in USD',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

# RAGAS scores (updated periodically)
ragas_faithfulness_score = Gauge(
    name='indogovrag_ragas_faithfulness',
    documentation='Current RAGAS faithfulness score'
)

ragas_relevancy_score = Gauge(
    name='indogovrag_ragas_answer_relevancy',
    documentation='Current RAGAS answer relevancy score'
)

# Retrieval confidence
retrieval_confidence = Histogram(
    name='indogovrag_retrieval_confidence',
    documentation='Average retrieval confidence score',
    buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
)

# === CACHE METRICS (BET-005) ===

# Cache requests
cache_requests_total = Counter(
    name='indogovrag_cache_requests_total',
    documentation='Total cache requests',
    labelnames=['result']  # hit, miss
)

# Cache similarity scores
cache_similarity_score = Histogram(
    name='indogovrag_cache_similarity',
    documentation='Cache hit similarity scores',
    buckets=[0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 1.0]
)

# Cache false positives
cache_false_positives_total = Counter(
    name='indogovrag_cache_false_positives_total',
    documentation='Total cache false positives reported'
)

# === COST METRICS (BET-006) ===

# Token usage tracking
llm_tokens_total = Counter(
    name='indogovrag_llm_tokens_total',
    documentation='Total LLM tokens consumed',
    labelnames=['type']  # input, output
)

# Cost savings from optimizations
cost_saved_usd = Counter(
    name='indogovrag_cost_saved_usd_total',
    documentation='Cumulative cost saved from compression and caching',
    labelnames=['source']  # compression, cache
)

# === QUALITY MONITORING (BET-008) ===

# Quality score per query (sampled)
query_quality_score = Histogram(
    name='indogovrag_query_quality_score',
    documentation='Quality score per query (sampled)',
    buckets=[0.5, 0.6, 0.7, 0.74, 0.8, 0.85, 0.9, 0.95, 1.0]
)

# Quality degradation alerts
quality_below_threshold_total = Counter(
    name='indogovrag_quality_below_threshold_total',
    documentation='Count of queries with quality below threshold',
    labelnames=['threshold']  # 0.70, 0.74, 0.80
)

# === SYSTEM INFO ===

system_info = Info(
    name='indogovrag_system',
    documentation='System build and version information'
)

# Set static system info
system_info.info({
    'version': '1.5.0-beta',
    'embedding_model': 'multilingual-e5-base',
    'vector_db': 'chromadb',
    'llm_provider': 'gemini'
})


# === HELPER FUNCTIONS ===

def track_query_success(model: str, endpoint: str = "/query"):
    """Increment successful query counter"""
    queries_total.labels(status='success', model=model, endpoint=endpoint).inc()


def track_query_error(error_type: str, endpoint: str = "/query"):
    """Increment error query counter"""
    queries_total.labels(status=error_type, model='none', endpoint=endpoint).inc()


def observe_latency(latency_seconds: float, endpoint: str = "/query"):
    """Record query latency"""
    query_latency_seconds.labels(endpoint=endpoint).observe(latency_seconds)


def observe_retrieval_latency(latency_seconds: float, method: str = "vector"):
    """Record retrieval latency"""
    retrieval_latency_seconds.labels(method=method).observe(latency_seconds)


def observe_llm_latency(latency_seconds: float, model: str):
    """Record LLM latency"""
    llm_latency_seconds.labels(model=model).observe(latency_seconds)


def observe_compression_latency(latency_seconds: float):
    """Record compression latency (BET-007)"""
    compression_latency_seconds.observe(latency_seconds)


def observe_cache_latency(latency_seconds: float):
    """Record cache lookup latency (BET-007)"""
    cache_latency_seconds.observe(latency_seconds)


def observe_cost(cost_usd: float):
    """Record query cost"""
    query_cost_usd.observe(cost_usd)


def observe_confidence(confidence: float):
    """Record retrieval confidence"""
    retrieval_confidence.observe(confidence)


def update_ragas_scores(faithfulness: float, relevancy: float):
    """Update RAGAS gauge metrics"""
    ragas_faithfulness_score.set(faithfulness)
    ragas_relevancy_score.set(relevancy)


# === CACHE METRICS HELPERS (BET-005) ===

def track_cache_hit(similarity: float):
    """Track cache hit with similarity score"""
    cache_requests_total.labels(result='hit').inc()
    cache_similarity_score.observe(similarity)


def track_cache_miss():
    """Track cache miss"""
    cache_requests_total.labels(result='miss').inc()


def track_cache_false_positive():
    """Track cache false positive"""
    cache_false_positives_total.inc()


# === COST METRICS HELPERS (BET-006) ===

def track_tokens(input_tokens: int, output_tokens: int):
    """Track token usage"""
    llm_tokens_total.labels(type='input').inc(input_tokens)
    llm_tokens_total.labels(type='output').inc(output_tokens)


def track_cost_savings(savings_usd: float, source: str):
    """Track cost savings from optimization"""
    cost_saved_usd.labels(source=source).inc(savings_usd)


# === QUALITY METRICS HELPERS (BET-008) ===

def track_quality_score(score: float):
    """Track quality score"""
    query_quality_score.observe(score)
    
    # Check thresholds
    if score < 0.74:
        quality_below_threshold_total.labels(threshold='0.74').inc()
    if score < 0.70:
        quality_below_threshold_total.labels(threshold='0.70').inc()
