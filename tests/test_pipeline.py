"""Testes para o pipeline de integração ponta a ponta."""

from unittest.mock import patch

from src.models.enriched_dossier import DadoPesquisado, EnrichedDossier
from src.models.redacted_dossier import RedactedDossier
from src.pipeline import executar_pipeline
from src.schemas.dossier_input import DossierInput


def test_executar_pipeline_completo(tmp_path):
    """Testa o pipeline completo com mocks."""
    dossier = DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )

    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, patch(
        "src.pipeline.redigir_relatorio"
    ) as mock_redacao, patch("src.pipeline.salvar_relatorio") as mock_output:
        mock_pesquisa.return_value = [
            DadoPesquisado(categoria="financeiro", descricao="Receita", valor="R$ 5M", fontes=[])
        ]

        mock_enriched = EnrichedDossier(
            dossier_input=dossier,
            dados_pesquisados=mock_pesquisa.return_value,
        )

        mock_redacted = RedactedDossier(
            enriched=mock_enriched,
            conteudo="# Relatório\n\nConteúdo.",
            tom_de_voz="formal",
            modelo_usado="claude-3-5-sonnet",
        )
        mock_redacao.return_value = mock_redacted
        mock_output.return_value = str(tmp_path / "relatorio.md")

        resultado = executar_pipeline(
            dossier,
            tom="formal",
            formato="markdown",
            output_path=str(tmp_path / "relatorio.md"),
        )

        assert resultado == str(tmp_path / "relatorio.md")
        mock_pesquisa.assert_called_once()
        mock_redacao.assert_called_once()
        mock_output.assert_called_once()
