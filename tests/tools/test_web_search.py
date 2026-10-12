"""Testes para a ferramenta de busca web."""

import pytest

from src.tools.web_search import SearchError, buscar_na_web


def test_buscar_na_web_retorna_lista():
    resultados = buscar_na_web("TechFlow Solutions empresa automação", max_results=3)
    assert isinstance(resultados, list)
    assert len(resultados) <= 3
    for r in resultados:
        assert "url" in r
        assert "titulo" in r


def test_buscar_na_web_resultado_vazio():
    resultados = buscar_na_web("empresa xyz inexistente 12345", max_results=2)
    assert isinstance(resultados, list)


def test_buscar_na_web_consulta_vazia():
    resultados = buscar_na_web("", max_results=2)
    assert resultados == []
