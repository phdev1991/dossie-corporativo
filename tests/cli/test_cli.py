"""Testes para a CLI de carregamento do dossiê."""

import json
from unittest.mock import patch

import pytest

from src.cli.main import carregar_dossier, main
from src.schemas.dossier_input import DossierInput


def test_carregar_dossier_valido():
    dossier = carregar_dossier("data/example_dossier.json")
    assert isinstance(dossier, DossierInput)
    assert dossier.empresa_nome == "TechFlow Solutions"


def test_carregar_dossier_arquivo_inexistente():
    with pytest.raises(FileNotFoundError):
        carregar_dossier("data/nao_existe.json")


def test_carregar_dossier_json_malformado(tmp_path):
    arquivo_invalido = tmp_path / "invalido.json"
    arquivo_invalido.write_text("{ json malformado")
    with pytest.raises(ValueError):
        carregar_dossier(str(arquivo_invalido))


def test_carregar_dossier_campos_ausentes(tmp_path):
    arquivo_incompleto = tmp_path / "incompleto.json"
    arquivo_incompleto.write_text('{"empresa_nome": "Empresa X"}')
    with pytest.raises(ValueError):
        carregar_dossier(str(arquivo_incompleto))


def test_redigir_relatorio_cli(tmp_path, monkeypatch, capsys):
    """Testa o subcomando redigir da CLI."""
    enriched_data = {
        "dossier_input": {
            "empresa_nome": "Empresa X",
            "segmento": "Tecnologia",
            "descricao": "Empresa de tecnologia focada em automação.",
        },
        "dados_pesquisados": [],
        "data_enriquecimento": "2026-10-12T10:00:00",
    }
    enriched_file = tmp_path / "enriched.json"
    enriched_file.write_text(json.dumps(enriched_data), encoding="utf-8")

    output_file = tmp_path / "relatorio.md"

    with patch("src.redacao.motor_redacao._chamar_llm") as mock_llm:
        mock_llm.return_value = ("# Relatório Empresa X\n\nConteúdo.", "claude-3-5-sonnet")
        monkeypatch.setattr(
            "sys.argv",
            ["main.py", "redigir", str(enriched_file), "--tom", "formal", "-o", str(output_file)],
        )
        main()

    captured = capsys.readouterr()
    assert "Relatório salvo" in captured.out
    assert "formal" in captured.out
    assert "markdown" in captured.out
    assert output_file.exists()
    conteudo = output_file.read_text(encoding="utf-8")
    assert "Dossiê Corporativo" in conteudo
    assert "Relatório Empresa X" in conteudo


def test_redigir_relatorio_html_cli(tmp_path, monkeypatch, capsys):
    """Testa o subcomando redigir com formato HTML."""
    enriched_data = {
        "dossier_input": {
            "empresa_nome": "Empresa X",
            "segmento": "Tecnologia",
            "descricao": "Empresa de tecnologia focada em automação.",
        },
        "dados_pesquisados": [],
        "data_enriquecimento": "2026-10-12T10:00:00",
    }
    enriched_file = tmp_path / "enriched.json"
    enriched_file.write_text(json.dumps(enriched_data), encoding="utf-8")

    output_file = tmp_path / "relatorio.html"

    with patch("src.redacao.motor_redacao._chamar_llm") as mock_llm:
        mock_llm.return_value = ("# Relatório Empresa X\n\nConteúdo.", "claude-3-5-sonnet")
        monkeypatch.setattr(
            "sys.argv",
            [
                "main.py", "redigir", str(enriched_file),
                "--tom", "consultivo", "--formato", "html",
                "-o", str(output_file),
            ],
        )
        main()

    captured = capsys.readouterr()
    assert "Relatório salvo" in captured.out
    assert "html" in captured.out
    assert output_file.exists()
    conteudo = output_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in conteudo
    assert "Empresa X" in conteudo
