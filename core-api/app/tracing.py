from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import os


def setup_tracing(service_name: str, app=None):
    """
    Sets up OpenTelemetry tracing for the service.
    """

    # 1. Define the resource (service name)
    resource = Resource.create(attributes={
        "service.name": service_name
    })

    # 2. Configure the Tracer Provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # 3. Configure the OTLP Exporter (sends traces to Jaeger)
    # It reads endpoint from OTEL_EXPORTER_OTLP_ENDPOINT env var
    otlp_exporter = OTLPSpanExporter()

    # 4. Add the exporter to the provider
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # 5. Instrument FastAPI (if app is provided)
    if app:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    # 6. Instrument Redis (Auto-instrumentation)
    RedisInstrumentor().instrument(tracer_provider=tracer_provider)

    print(f"Tracing initialized for {service_name}")