"""Testes para o modelo EnrichedDossier."""

import pytest

from src.models.enriched_dossier import DadoPesquisado, EnrichedDossier, FonteEncontrada
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def dossier_input():
    return DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )


def test_fonte_encontrada_campos():
    fonte = FonteEncontrada(
        url="https://exemplo.com",
        titulo="Título",
        trecho="Trecho da informação.",
        confiabilidade="alta",
    )
    assert fonte.url == "https://exemplo.com"


def test_dado_pesquisado_campos():
    dado = DadoPesquisado(
        categoria="financeiro",
        descricao="Receita anual",
        valor="R$ 5M",
        fontes=[],
    )
    assert dado.conflito is False


def test_enriched_dossier_total_fontes(dossier_input):
    dado = DadoPesquisado(
        categoria="financeiro",
        descricao="Receita",
        valor=None,
        fontes=[
            FonteEncontrada(url="https://a.com", titulo="A", trecho="x", confiabilidade="alta"),
            FonteEncontrada(url="https://b.com", titulo="B", trecho="y", confiabilidade="media"),
        ],
    )
    enriched = EnrichedDossier(dossier_input=dossier_input, dados_pesquisados=[dado])
    assert enriched.total_fontes == 2


def test_enriched_dossier_to_dict(dossier_input):
    enriched = EnrichedDossier(dossier_input=dossier_input, dados_pesquisados=[])
    result = enriched.to_dict()
    assert isinstance(result, dict)
    assert "dossier_input" in result
    assert "total_fontes" in result
