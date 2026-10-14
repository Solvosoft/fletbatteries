"""Integración con FastAPI (requiere el extra `fletbatteries[api]`)."""

from fletbatteries.api.auth import auth_router, current_api_user, require_perms  # noqa: F401
from fletbatteries.api.crud_router import crud_router, parse_filters, schema_from_model  # noqa: F401
