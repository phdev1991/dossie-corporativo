"""Testes para a skill de output."""

import pytest

from src.models.enriched_dossier import EnrichedDossier
from src.models.redacted_dossier import RedactedDossier
from src.output.skill_output import (
    formatar_relatorio_html,
    formatar_relatorio_markdown,
    salvar_relatorio,
)
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def redacted():
    return RedactedDossier(
        enriched=EnrichedDossier(
            dossier_input=DossierInput(
                empresa_nome="Empresa X",
                segmento="Tecnologia",
                descricao="Empresa de tecnologia focada em automação.",
            ),
            dados_pesquisados=[],
        ),
        conteudo="# Relatório Empresa X\n\nConteúdo do relatório.",
        tom_de_voz="formal",
        modelo_usado="claude-3-5-sonnet",
    )


def test_formatar_relatorio_markdown(redacted):
    resultado = formatar_relatorio_markdown(redacted)
    assert "Dossiê Corporativo — Empresa X" in resultado
    assert "Tecnologia" in resultado
    assert "formal" in resultado
    assert "claude-3-5-sonnet" in resultado
    assert "Relatório Empresa X" in resultado


def test_formatar_relatorio_html(redacted):
    resultado = formatar_relatorio_html(redacted)
    assert "<!DOCTYPE html>" in resultado
    assert "Empresa X" in resultado
    assert "formal" in resultado


def test_salvar_relatorio_markdown(redacted, tmp_path):
    output = tmp_path / "relatorio.md"
    caminho = salvar_relatorio(redacted, str(output), formato="markdown")
    assert caminho == str(output) or caminho == str(output)
    assert output.exists()
    conteudo = output.read_text(encoding="utf-8")
    assert "Dossiê Corporativo" in conteudo


def test_salvar_relatorio_html(redacted, tmp_path):
    output = tmp_path / "relatorio.html"
    salvar_relatorio(redacted, str(output), formato="html")
    assert output.exists()
    conteudo = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in conteudo


def test_salvar_relatorio_formato_invalido(redacted, tmp_path):
    with pytest.raises(ValueError):
        salvar_relatorio(redacted, str(tmp_path / "r.txt"), formato="pdf")


def test_salvar_relatorio_adiciona_extensao(redacted, tmp_path):
    output = tmp_path / "relatorio"
    salvar_relatorio(redacted, str(output), formato="markdown")
    assert (tmp_path / "relatorio.md").exists()
