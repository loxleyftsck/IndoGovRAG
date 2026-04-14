"""
OpenTelemetry Tracing for IndoGovRAG
Production-ready distributed tracing implementation

Best Practices References:
- https://opentelemetry.io/docs/instrumentation/python/
- https://opentelemetry.io/docs/specs/otel/trace/semantic_conventions/
"""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.semconv.resource import ResourceAttributes

def setup_tracing(service_name: str = "indogovrag", environment: str = "production"):
    """
    Setup OpenTelemetry tracing with Jaeger exporter
    
    Args:
        service_name: Name of the service (appears in Jaeger UI)
        environment: Deployment environment (production/staging/dev)
    
    Returns:
        Tracer instance for manual instrumentation
    """
    
    # Create resource with service metadata
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0-beta",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: environment,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
        agent_port=int(os.getenv("JAEGER_PORT", 6831)),
    )
    
    # Add span processor (batch for performance)
    provider.add_span_processor(
        BatchSpanProcessor(
            jaeger_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
        )
    )
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    print(f"✅ Tracing initialized: service={service_name}, env={environment}")
    
    return trace.get_tracer(__name__)


# Global tracer instance
tracer = setup_tracing()


def trace_rag_operation(operation_name: str):
    """
    Decorator for tracing RAG pipeline operations
    
    Usage:
        @trace_rag_operation("retrieval")
        def search_documents(query):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(operation_name) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
        return wrapper
    return decorator
