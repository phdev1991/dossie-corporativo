"""Testes para erros do pipeline."""

from unittest.mock import patch

import pytest

from src.models.enriched_dossier import DadoPesquisado, EnrichedDossier
from src.models.redacted_dossier import RedactedDossier
from src.pipeline import PipelineError, executar_pipeline
from src.schemas.dossier_input import DossierInput


def _dossier() -> DossierInput:
    return DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )


def test_pipeline_erro_na_pesquisa(tmp_path):
    """PipelineError quando a pesquisa falha."""
    dossier = _dossier()

    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa:
        mock_pesquisa.side_effect = Exception("Falha na busca")
        with pytest.raises(PipelineError, match="Pesquisa"):
            executar_pipeline(dossier, output_path=str(tmp_path / "relatorio.md"))


def test_pipeline_erro_na_redacao(tmp_path):
    """PipelineError quando a redação falha."""
    dossier = _dossier()

    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, patch(
        "src.pipeline.redigir_relatorio"
    ) as mock_redacao:
        mock_pesquisa.return_value = [
            DadoPesquisado(categoria="financeiro", descricao="Receita", valor="R$ 5M", fontes=[])
        ]
        mock_redacao.side_effect = RuntimeError("LLM indisponível")
        with pytest.raises(PipelineError, match="Redação"):
            executar_pipeline(dossier, output_path=str(tmp_path / "relatorio.md"))


def test_pipeline_erro_no_output(tmp_path):
    """PipelineError quando o output falha."""
    dossier = _dossier()
    dados = [
        DadoPesquisado(categoria="financeiro", descricao="Receita", valor="R$ 5M", fontes=[])
    ]
    enriched = EnrichedDossier(dossier_input=dossier, dados_pesquisados=dados)
    redacted = RedactedDossier(
        enriched=enriched,
        conteudo="# Relatório\n\nConteúdo.",
        tom_de_voz="formal",
        modelo_usado="claude-3-5-sonnet",
    )

    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, patch(
        "src.pipeline.redigir_relatorio"
    ) as mock_redacao, patch("src.pipeline.salvar_relatorio") as mock_output:
        mock_pesquisa.return_value = dados
        mock_redacao.return_value = redacted
        mock_output.side_effect = ValueError("Formato não suportado")
        with pytest.raises(PipelineError, match="Output"):
            executar_pipeline(
                dossier, formato="pdf", output_path=str(tmp_path / "relatorio.pdf")
            )


def test_pipeline_erro_nao_encapsulado_quando_tudo_ok(tmp_path):
    """Não levanta PipelineError quando tudo funciona."""
    dossier = _dossier()
    dados = [
        DadoPesquisado(categoria="financeiro", descricao="Receita", valor="R$ 5M", fontes=[])
    ]
    enriched = EnrichedDossier(dossier_input=dossier, dados_pesquisados=dados)
    redacted = RedactedDossier(
        enriched=enriched,
        conteudo="# Relatório\n\nConteúdo.",
        tom_de_voz="formal",
        modelo_usado="claude-3-5-sonnet",
    )

    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, patch(
        "src.pipeline.redigir_relatorio"
    ) as mock_redacao, patch("src.pipeline.salvar_relatorio") as mock_output:
        mock_pesquisa.return_value = dados
        mock_redacao.return_value = redacted
        mock_output.return_value = str(tmp_path / "relatorio.md")

        resultado = executar_pipeline(
            dossier, output_path=str(tmp_path / "relatorio.md")
        )

        assert resultado == str(tmp_path / "relatorio.md")
