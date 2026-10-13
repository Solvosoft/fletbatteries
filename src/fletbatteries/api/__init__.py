"""Integración con FastAPI (requiere el extra `fletbatteries[api]`)."""

from fletbatteries.api.crud_router import crud_router, parse_filters, schema_from_model  # noqa: F401
