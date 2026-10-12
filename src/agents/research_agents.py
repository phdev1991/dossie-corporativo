"""Subagentes de pesquisa externa para enriquecimento do dossiê."""

import logging

from crewai import Agent

from src.models.enriched_dossier import DadoPesquisado
from src.schemas.dossier_input import DossierInput
from src.tools.web_search import SearchError, buscar_na_web

logger = logging.getLogger(__name__)


def _criar_agente(role: str, goal: str, backstory: str) -> Agent:
    """Cria um agente CrewAI com configuração padrão."""
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=False,
        allow_delegation=False,
    )


def pesquisar_dados(dossier: DossierInput) -> list[DadoPesquisado]:
    """Orquestra os subagentes de pesquisa para enriquecer o dossiê.

    Args:
        dossier: Dossiê de entrada validado.

    Returns:
        Lista de dados pesquisados com fontes.
    """
    agentes = [
        _criar_agente(
            role="Pesquisador Financeiro",
            goal=f"Encontrar dados financeiros da empresa {dossier.empresa_nome}",
            backstory="Especialista em análise financeira e dados corporativos.",
        ),
        _criar_agente(
            role="Pesquisador de Concorrentes",
            goal=f"Identificar concorrentes da {dossier.empresa_nome} no segmento {dossier.segmento}",
            backstory="Analista de mercado especialista em inteligência competitiva.",
        ),
        _criar_agente(
            role="Pesquisador de Mercado",
            goal=f"Coletar dados de mercado do segmento {dossier.segmento}",
            backstory="Especialista em tendências de mercado e análise setorial.",
        ),
    ]

    resultados = []
    for agente in agentes:
        try:
            consulta = f"{dossier.empresa_nome} {dossier.segmento} dados empresa"
            resultados_web = buscar_na_web(consulta)
            dado = DadoPesquisado(
                categoria=agente.role,
                descricao=f"Dados encontrados para {agente.role}",
                fontes=[
                    {
                        "url": r["url"],
                        "titulo": r["titulo"],
                        "trecho": r["trecho"],
                        "confiabilidade": "media",
                    }
                    for r in resultados_web
                ],
            )
            resultados.append(dado)
        except SearchError as e:
            logger.warning(f"Subagente {agente.role} falhou: {e}")
    return resultados
