"""Ferramenta de busca web para os subagentes de pesquisa."""

import logging

from ddgs import DDGS
from ddgs.exceptions import DDGSException

from config.settings import settings

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Erro durante a busca web."""


def buscar_na_web(consulta: str, max_results: int | None = None) -> list[dict]:
    """Busca informações na web usando DuckDuckGo.

    Args:
        consulta: Termo de busca.
        max_results: Número máximo de resultados (padrão: settings.search_max_results).

    Returns:
        Lista de dicts com url, titulo, trecho. Lista vazia se não houver resultados.

    Raises:
        SearchError: Se a busca falhar por motivo diferente de "sem resultados".
    """
    if not consulta.strip():
        return []
    max_results = max_results or settings.search_max_results
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=max_results))
    except DDGSException as e:
        msg = str(e).lower()
        if "no results" in msg or "not found" in msg:
            logger.info(f"Busca sem resultados: {consulta}")
            return []
        logger.warning(f"Busca web falhou: {e}")
        raise SearchError(f"Erro na busca: {e}") from e
    except Exception as e:
        logger.warning(f"Busca web falhou: {e}")
        raise SearchError(f"Erro na busca: {e}") from e

    return [
        {
            "url": r.get("href", ""),
            "titulo": r.get("title", ""),
            "trecho": r.get("body", ""),
        }
        for r in resultados
    ]
