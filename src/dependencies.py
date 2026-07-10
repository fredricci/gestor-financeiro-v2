"""Dependências compartilhadas do FastAPI."""

from functools import lru_cache

from src.config import settings
from src.services.claude_client import AnthropicCategorizer, Categorizer


@lru_cache
def _categorizer_singleton() -> AnthropicCategorizer:
    return AnthropicCategorizer(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
    )


def get_categorizer() -> Categorizer:
    """Fornece o categorizador por IA (sobrescrito nos testes por um fake)."""
    return _categorizer_singleton()
