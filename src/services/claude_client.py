"""Cliente da Claude API para categorização em lote.

Define a interface `Categorizer` (para permitir mock nos testes) e a
implementação real `AnthropicCategorizer`. Em caso de erro na API ou no
parsing, retorna um fallback com categoria 'NAO LEMBRO' / origem 'erro'.
"""

from typing import Protocol

from src.logging_config import get_logger
from src.services.prompts import construir_prompt, parse_resposta_ia

logger = get_logger(__name__)


def _fallback(itens: list[dict]) -> list[dict]:
    return [
        {
            "descricao": it["descricao"],
            "categoria": "NAO LEMBRO",
            "subcategoria": "",
            "confianca": "baixa",
            "origem": "erro",
            "tipo_valor": it.get("tipo_valor", "saida"),
        }
        for it in itens
    ]


class Categorizer(Protocol):
    """Contrato de um categorizador por IA."""

    async def categorizar(
        self, itens: list[dict], historico: list[tuple[str, str, str]]
    ) -> list[dict]:
        ...


class AnthropicCategorizer:
    """Implementação real usando a Claude API (async)."""

    def __init__(self, api_key: str, model: str, max_tokens: int = 2000) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens

    async def categorizar(
        self, itens: list[dict], historico: list[tuple[str, str, str]]
    ) -> list[dict]:
        if not itens:
            return []
        if not self._api_key:
            logger.warning("anthropic_sem_api_key", n_itens=len(itens))
            return _fallback(itens)

        prompt = construir_prompt(itens, historico)
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self._api_key)
            msg = await client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            texto = msg.content[0].text
            return parse_resposta_ia(texto, itens)
        except Exception as exc:  # noqa: BLE001 — degrada graciosamente
            logger.error("erro_categorizacao_ia", erro=str(exc), tipo=type(exc).__name__)
            return _fallback(itens)
