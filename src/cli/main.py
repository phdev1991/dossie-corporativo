"""CLI para carregar, validar e enriquecer o dossiê corporativo."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from src.schemas.dossier_input import DossierInput


def carregar_dossier(caminho: str) -> DossierInput:
    """Carrega e valida um dossiê corporativo a partir de um arquivo JSON.

    Args:
        caminho: Caminho do arquivo JSON do dossiê.

    Returns:
        DossierInput validado.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o JSON estiver malformado ou o dossiê for inválido.
    """
    path = Path(caminho)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON malformado: {e}") from e
    try:
        return DossierInput(**data)
    except ValidationError as e:
        raise ValueError(f"Dossiê inválido: {e}") from e


def cmd_carregar(args: argparse.Namespace) -> None:
    """Executa o subcomando `carregar`."""
    try:
        dossier = carregar_dossier(args.caminho)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Dossiê carregado: {dossier.empresa_nome}")
    print(f"Segmento: {dossier.segmento}")
    print(f"Fontes conhecidas: {len(dossier.fontes_conhecidas)}")


def cmd_pesquisar(args: argparse.Namespace) -> None:
    """Executa o subcomando `pesquisar`."""
    from src.agents.research_agents import pesquisar_dados
    from src.models.enriched_dossier import EnrichedDossier

    try:
        dossier = carregar_dossier(args.caminho)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Pesquisando dados para: {dossier.empresa_nome}")
    dados = pesquisar_dados(dossier)
    enriched = EnrichedDossier(dossier_input=dossier, dados_pesquisados=dados)

    output = args.output or "data/enriched_dossier.json"
    Path(output).write_text(
        json.dumps(enriched.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Dossiê enriquecido salvo em: {output}")
    print(f"Total de fontes: {enriched.total_fontes}")


def cmd_redigir(args: argparse.Namespace) -> None:
    """Executa o subcomando `redigir`."""
    from src.models.enriched_dossier import EnrichedDossier
    from src.redacao.motor_redacao import redigir_relatorio
    from src.output.skill_output import salvar_relatorio

    path = Path(args.caminho)
    if not path.exists():
        print(f"Erro: Arquivo não encontrado: {args.caminho}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Erro: JSON malformado: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        enriched = EnrichedDossier(**data)
    except Exception as e:
        print(f"Erro: Dossiê enriquecido inválido: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        redacted = redigir_relatorio(enriched, tom=args.tom)
    except (ValueError, RuntimeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    output = args.output or "data/relatorio"
    try:
        caminho = salvar_relatorio(redacted, output, formato=args.formato)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Relatório salvo em: {caminho}")
    print(f"Tom de voz: {redacted.tom_de_voz}")
    print(f"Modelo: {redacted.modelo_usado}")
    print(f"Formato: {args.formato}")


def cmd_pipeline(args: argparse.Namespace) -> None:
    """Executa o subcomando `pipeline` (fluxo completo)."""
    from src.pipeline import PipelineError, executar_pipeline

    try:
        dossier = carregar_dossier(args.caminho)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Executando pipeline para: {dossier.empresa_nome}")
    try:
        caminho = executar_pipeline(
            dossier,
            tom=args.tom,
            formato=args.formato,
            output_path=args.output or "data/relatorio",
        )
    except PipelineError as e:
        print(f"Erro no pipeline: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Pipeline concluído: {caminho}")
    print(f"Tom de voz: {args.tom}")
    print(f"Formato: {args.formato}")


def main() -> None:
    """Ponto de entrada da CLI."""
    parser = argparse.ArgumentParser(description="Projeto Dossiê Corporativo")
    subparsers = parser.add_subparsers(dest="comando")

    parser_carregar = subparsers.add_parser("carregar", help="Carregar dossiê")
    parser_carregar.add_argument("caminho", help="Caminho do JSON do dossiê")
    parser_carregar.set_defaults(func=cmd_carregar)

    parser_pesquisar = subparsers.add_parser("pesquisar", help="Pesquisar dados externos")
    parser_pesquisar.add_argument("caminho", help="Caminho do JSON do dossiê")
    parser_pesquisar.add_argument("--output", "-o", help="Caminho do JSON de saída")
    parser_pesquisar.set_defaults(func=cmd_pesquisar)

    parser_redigir = subparsers.add_parser("redigir", help="Redigir relatório executivo")
    parser_redigir.add_argument("caminho", help="Caminho do JSON do dossiê enriquecido")
    parser_redigir.add_argument(
        "--tom",
        choices=["formal", "consultivo", "tecnico"],
        default="formal",
        help="Tom de voz do relatório",
    )
    parser_redigir.add_argument(
        "--formato",
        choices=["markdown", "html"],
        default="markdown",
        help="Formato de saída",
    )
    parser_redigir.add_argument("--output", "-o", help="Caminho do arquivo de saída")
    parser_redigir.set_defaults(func=cmd_redigir)

    parser_pipeline = subparsers.add_parser("pipeline", help="Pipeline completo")
    parser_pipeline.add_argument("caminho", help="Caminho do JSON do dossiê")
    parser_pipeline.add_argument(
        "--tom",
        choices=["formal", "consultivo", "tecnico"],
        default="formal",
        help="Tom de voz do relatório",
    )
    parser_pipeline.add_argument(
        "--formato",
        choices=["markdown", "html"],
        default="markdown",
        help="Formato de saída",
    )
    parser_pipeline.add_argument("--output", "-o", help="Caminho do arquivo de saída")
    parser_pipeline.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
