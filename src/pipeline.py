"""Pipeline de integração ponta a ponta do Projeto Dossiê Corporativo."""

import logging

from src.agents.research_agents import pesquisar_dados
from src.models.enriched_dossier import EnrichedDossier
from src.output.skill_output import salvar_relatorio
from src.redacao.motor_redacao import redigir_relatorio
from src.schemas.dossier_input import DossierInput

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Erro durante a execução do pipeline."""


def executar_pipeline(
    dossier: DossierInput,
    tom: str = "formal",
    formato: str = "markdown",
    output_path: str = "data/relatorio",
) -> str:
    """Executa o pipeline completo: pesquisa → redação → output.

    Args:
        dossier: Dossiê de entrada validado.
        tom: Tom de voz do relatório (formal, consultivo, tecnico).
        formato: Formato de saída (markdown ou html).
        output_path: Caminho do arquivo de saída.

    Returns:
        Caminho do arquivo gerado.

    Raises:
        PipelineError: Se o pipeline falhar.
    """
    logger.info(f"Iniciando pipeline para {dossier.empresa_nome}")

    # 1. Pesquisa
    logger.info("Fase 1/3: Pesquisando dados externos...")
    try:
        dados_pesquisados = pesquisar_dados(dossier)
        logger.info(f"Pesquisa concluída: {len(dados_pesquisados)} dados encontrados")
    except Exception as e:
        logger.error(f"Falha na pesquisa: {e}")
        raise PipelineError(f"Pesquisa: {e}") from e

    # 2. Enriquecimento
    enriched = EnrichedDossier(
        dossier_input=dossier,
        dados_pesquisados=dados_pesquisados,
    )

    # 3. Redação
    logger.info(f"Fase 2/3: Redigindo relatório (tom: {tom})...")
    try:
        redacted = redigir_relatorio(enriched, tom=tom)
        logger.info("Redação concluída")
    except Exception as e:
        logger.error(f"Falha na redação: {e}")
        raise PipelineError(f"Redação: {e}") from e

    # 4. Output
    logger.info(f"Fase 3/3: Salvando relatório ({formato})...")
    try:
        caminho = salvar_relatorio(redacted, output_path, formato=formato)
        logger.info(f"Pipeline concluído: {caminho}")
    except Exception as e:
        logger.error(f"Falha no output: {e}")
        raise PipelineError(f"Output: {e}") from e

    return caminho
