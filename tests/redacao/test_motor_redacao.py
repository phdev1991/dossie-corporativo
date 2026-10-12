"""Testes para o motor de redação comercial."""

import pytest
from unittest.mock import patch

from src.models.enriched_dossier import DadoPesquisado, EnrichedDossier
from src.redacao.motor_redacao import redigir_relatorio
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def enriched():
    return EnrichedDossier(
        dossier_input=DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
        ),
        dados_pesquisados=[
            DadoPesquisado(
                categoria="financeiro",
                descricao="Receita anual",
                valor="R$ 5M",
                fontes=[],
            )
        ],
    )


@patch("src.redacao.motor_redacao._chamar_llm")
def test_redigir_relatorio(mock_llm, enriched):
    mock_llm.return_value = ("# Relatório Empresa X\n\nConteúdo gerado.", "claude-3-5-sonnet")
    resultado = redigir_relatorio(enriched, tom="formal")
    assert resultado.tom_de_voz == "formal"
    assert "Relatório" in resultado.conteudo
    assert resultado.modelo_usado


@patch("src.redacao.motor_redacao._chamar_llm")
def test_redigir_relatorio_dados_vazios(mock_llm, enriched):
    enriched.dados_pesquisados = []
    mock_llm.return_value = ("# Relatório\n\nSem dados disponíveis.", "claude-3-5-sonnet")
    resultado = redigir_relatorio(enriched, tom="consultivo")
    assert resultado.tom_de_voz == "consultivo"


def test_redigir_relatorio_tom_invalido(enriched):
    with pytest.raises(ValueError):
        redigir_relatorio(enriched, tom="informal")
