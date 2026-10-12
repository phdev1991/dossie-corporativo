"""Testes para o subcomando `pipeline` da CLI."""

import json
from unittest.mock import patch

from src.cli.main import main


def test_pipeline_completo_cli(tmp_path, monkeypatch, capsys):
    """Testa o pipeline completo via CLI com mocks."""
    dossier_data = {
        "empresa_nome": "Empresa X",
        "segmento": "Tecnologia",
        "descricao": "Empresa de tecnologia focada em automação.",
    }
    dossier_file = tmp_path / "dossier.json"
    dossier_file.write_text(json.dumps(dossier_data), encoding="utf-8")

    output_file = tmp_path / "relatorio.md"

    with patch("src.pipeline.executar_pipeline") as mock_pipeline:
        mock_pipeline.return_value = str(output_file)
        monkeypatch.setattr(
            "sys.argv",
            [
                "main.py", "pipeline", str(dossier_file),
                "--tom", "consultivo", "--formato", "markdown",
                "-o", str(output_file),
            ],
        )
        main()

    captured = capsys.readouterr()
    assert "Executando pipeline" in captured.out
    assert "Pipeline concluído" in captured.out
    assert "consultivo" in captured.out
    assert "markdown" in captured.out
    mock_pipeline.assert_called_once()


def test_pipeline_cli_arquivo_inexistente(tmp_path, monkeypatch, capsys):
    """Testa pipeline com arquivo inexistente."""
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "pipeline", str(tmp_path / "nao_existe.json")],
    )
    try:
        main()
    except SystemExit as e:
        assert e.code == 1
    captured = capsys.readouterr()
    assert "Erro" in captured.err


def test_pipeline_cli_erro_pipeline(tmp_path, monkeypatch, capsys):
    """Testa pipeline com falha na execução."""
    from src.pipeline import PipelineError

    dossier_data = {
        "empresa_nome": "Empresa X",
        "segmento": "Tecnologia",
        "descricao": "Empresa de tecnologia focada em automação.",
    }
    dossier_file = tmp_path / "dossier.json"
    dossier_file.write_text(json.dumps(dossier_data), encoding="utf-8")

    with patch("src.pipeline.executar_pipeline") as mock_pipeline:
        mock_pipeline.side_effect = PipelineError("Pesquisa: falha na busca")
        monkeypatch.setattr(
            "sys.argv",
            ["main.py", "pipeline", str(dossier_file)],
        )
        try:
            main()
        except SystemExit as e:
            assert e.code == 1

    captured = capsys.readouterr()
    assert "Erro no pipeline" in captured.err
