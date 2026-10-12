"""Testes ponta a ponta (E2E) com dossiê real."""

import json
from unittest.mock import patch

from src.models.enriched_dossier import DadoPesquisado, FonteEncontrada
from src.pipeline import executar_pipeline


def test_pipeline_e2e_com_dossier_real(tmp_path):
    """Pipeline completo com dossiê real, buscando web e redigindo com LLM mockado."""
    from src.cli.main import carregar_dossier

    dossier = carregar_dossier("data/example_dossier.json")

    dados_mock = [
        DadoPesquisado(
            categoria="mercado",
            descricao="Setor de automação corporativa",
            valor="Crescimento de 15% ao ano no Brasil",
            fontes=[
                FonteEncontrada(
                    url="https://exemplo.com/mercado",
                    titulo="Mercado de Automação",
                    trecho="Crescimento projetado",
                    confiabilidade="media",
                )
            ],
        ),
        DadoPesquisado(
            categoria="financeiro",
            descricao="Receita anual declarada",
            valor="R$ 5.000.000,00",
            fontes=[
                FonteEncontrada(
                    url="https://techflow.com.br",
                    titulo="TechFlow Solutions",
                    trecho="Receita declarada",
                    confiabilidade="alta",
                )
            ],
        ),
    ]

    output = tmp_path / "relatorio.md"

    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, patch(
        "src.redacao.motor_redacao._chamar_llm"
    ) as mock_llm:
        mock_pesquisa.return_value = dados_mock
        mock_llm.return_value = (
            "# Análise Executiva — TechFlow Solutions\n\n"
            "## Panorama Geral\n\n"
            "A TechFlow Solutions atua em automação corporativa.\n\n"
            "## Dados Financeiros\n\n"
            "Receita anual de R$ 5.000.000,00.\n\n"
            "## Conclusão\n\n"
            "Empresa em expansão no mercado B2B.",
            "claude-3-5-sonnet-mock",
        )

        caminho = executar_pipeline(
            dossier,
            tom="consultivo",
            formato="markdown",
            output_path=str(output),
        )

    assert caminho == str(output)
    assert output.exists()

    conteudo = output.read_text(encoding="utf-8")
    assert "TechFlow Solutions" in conteudo
    assert "Dossiê Corporativo" in conteudo
    assert "consultivo" in conteudo
    assert "claude-3-5-sonnet-mock" in conteudo
    assert "Análise Executiva" in conteudo


def test_pipeline_e2e_formato_html(tmp_path):
    """Pipeline completo gerando HTML a partir do dossiê real."""
    from src.cli.main import carregar_dossier

    dossier = carregar_dossier("data/example_dossier.json")

    output = tmp_path / "relatorio.html"

    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, patch(
        "src.redacao.motor_redacao._chamar_llm"
    ) as mock_llm:
        mock_pesquisa.return_value = [
            DadoPesquisado(
                categoria="mercado",
                descricao="Setor de automação",
                valor="Crescimento de 15%",
                fontes=[
                    FonteEncontrada(
                        url="https://exemplo.com",
                        titulo="Mercado",
                        trecho="Crescimento",
                        confiabilidade="media",
                    )
                ],
            )
        ]
        mock_llm.return_value = ("# Relatório\n\nConteúdo.", "mock-model")

        caminho = executar_pipeline(
            dossier,
            tom="tecnico",
            formato="html",
            output_path=str(output),
        )

    assert caminho == str(output)
    assert output.exists()

    conteudo = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in conteudo
    assert "TechFlow Solutions" in conteudo
    assert "tecnico" in conteudo
