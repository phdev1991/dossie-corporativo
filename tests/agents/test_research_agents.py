"""Testes para os subagentes de pesquisa externa."""

from unittest.mock import patch

import pytest

from src.agents.research_agents import pesquisar_dados
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def dossier_input():
    return DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )


@patch("src.agents.research_agents.buscar_na_web")
def test_pesquisar_dados_retorna_lista(mock_buscar, dossier_input):
    mock_buscar.return_value = [
        {"url": "https://exemplo.com", "titulo": "Exemplo", "trecho": "Dados da empresa."}
    ]
    resultados = pesquisar_dados(dossier_input)
    assert isinstance(resultados, list)
    assert len(resultados) == 3  # um por agente: financeiro, concorrentes, mercado


@patch("src.agents.research_agents.buscar_na_web")
def test_pesquisar_dados_empresa_desconhecida(mock_buscar, dossier_input):
    mock_buscar.return_value = []
    resultados = pesquisar_dados(dossier_input)
    assert isinstance(resultados, list)
    assert len(resultados) == 3  # agentes ainda retornam dados, mas sem fontes


@patch("src.agents.research_agents.buscar_na_web")
def test_pesquisar_dados_busca_falha(mock_buscar, dossier_input):
    from src.tools.web_search import SearchError

    mock_buscar.side_effect = SearchError("timeout")
    resultados = pesquisar_dados(dossier_input)
    # Nenhum agente deve falhar o pipeline inteiro
    assert isinstance(resultados, list)
