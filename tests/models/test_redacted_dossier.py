"""Testes para o modelo RedactedDossier."""

import pytest

from src.models.enriched_dossier import EnrichedDossier
from src.models.redacted_dossier import RedactedDossier
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def enriched():
    return EnrichedDossier(
        dossier_input=DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
        ),
        dados_pesquisados=[],
    )


def test_redacted_dossier_campos(enriched):
    redacted = RedactedDossier(
        enriched=enriched,
        conteudo="# Relatório\n\nConteúdo do relatório.",
        tom_de_voz="formal",
        modelo_usado="claude-3-5-sonnet",
    )
    assert redacted.tom_de_voz == "formal"
    assert "Relatório" in redacted.conteudo


def test_redacted_dossier_to_dict(enriched):
    redacted = RedactedDossier(
        enriched=enriched,
        conteudo="# Relatório",
        tom_de_voz="consultivo",
        modelo_usado="gpt-4o",
    )
    result = redacted.to_dict()
    assert isinstance(result, dict)
    assert "conteudo" in result
    assert "tom_de_voz" in result
