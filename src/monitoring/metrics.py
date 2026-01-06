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

# === SYSTEM INFO ===

system_info = Info(
    name='indogovrag_system',
    documentation='System build and version information'
)

# Set static system info
system_info.info({
    'version': '1.0.0-beta',
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
