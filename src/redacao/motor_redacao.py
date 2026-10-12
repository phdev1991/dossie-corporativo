"""Motor de redação comercial — gera relatório executivo via LLM."""

import logging
from typing import Literal

from src.models.enriched_dossier import EnrichedDossier
from src.models.redacted_dossier import RedactedDossier
from src.redacao.tons_de_voz import obter_diretrizes, validar_tom

logger = logging.getLogger(__name__)


def _montar_prompt(enriched: EnrichedDossier, tom: str) -> str:
    """Monta o prompt estruturado para a LLM."""
    d = enriched.dossier_input
    linhas = [
        f"Você é um redator corporativo especializado em relatórios executivos.",
        f"",
        f"## Dados da Empresa",
        f"- Nome: {d.empresa_nome}",
        f"- Segmento: {d.segmento}",
        f"- Descrição: {d.descricao}",
    ]

    if d.cnpj:
        linhas.append(f"- CNPJ: {d.cnpj}")
    if d.dados_financeiros:
        linhas.append(f"- Dados financeiros: {d.dados_financeiros}")
    if d.fontes_conhecidas:
        linhas.append(f"- Fontes conhecidas: {', '.join(d.fontes_conhecidas)}")
    if d.notas_adicionais:
        linhas.append(f"- Notas: {d.notas_adicionais}")

    linhas.append("")
    linhas.append("## Dados Pesquisados")

    if enriched.dados_pesquisados:
        for dado in enriched.dados_pesquisados:
            linhas.append(f"- [{dado.categoria}] {dado.descricao}")
            if dado.valor:
                linhas.append(f"  Valor: {dado.valor}")
            if dado.conflito:
                linhas.append(f"  ⚠ Conflito detectado")
    else:
        linhas.append("- Nenhum dado pesquisado disponível.")

    linhas.append("")
    linhas.append("## Diretrizes de Tom de Voz")
    linhas.append(obter_diretrizes(tom))

    linhas.append("")
    linhas.append(
        "## Instruções\n"
        "Gere um relatório executivo em Markdown, em português, com as seções:\n"
        "1. Resumo Executivo\n"
        "2. Perfil da Empresa\n"
        "3. Dados de Mercado\n"
        "4. Análise Financeira\n"
        "5. Conclusão e Recomendações\n\n"
        "Se não houver dados para uma seção, escreva 'Não disponível'.\n"
        "NÃO inventa dados — use apenas os dados fornecidos acima."
    )

    return "\n".join(linhas)


def _chamar_anthropic(prompt: str, max_tokens: int = 4096) -> str:
    """Chama a API da Anthropic (Claude)."""
    import anthropic
    from config.settings import settings

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _chamar_openai(prompt: str, max_tokens: int = 4096) -> str:
    """Chama a API da OpenAI."""
    from openai import OpenAI
    from config.settings import settings

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def _chamar_llm(prompt: str, max_tokens: int = 4096) -> tuple[str, str]:
    """Chama a LLM configurada e retorna (texto, modelo)."""
    from config.settings import settings

    if settings.llm_provider == "anthropic":
        texto = _chamar_anthropic(prompt, max_tokens)
        return texto, settings.llm_model
    elif settings.llm_provider == "openai":
        texto = _chamar_openai(prompt, max_tokens)
        return texto, settings.llm_model
    else:
        raise ValueError(f"Provider não suportado: {settings.llm_provider}")


def redigir_relatorio(
    enriched: EnrichedDossier,
    tom: Literal["formal", "consultivo", "tecnico"] = "formal",
) -> RedactedDossier:
    """Gera o relatório executivo a partir do dossiê enriquecido.

    Args:
        enriched: Dossiê com dados pesquisados.
        tom: Tom de voz desejado.

    Returns:
        RedactedDossier com o conteúdo gerado.

    Raises:
        ValueError: Se o tom de voz for inválido.
        RuntimeError: Se a LLM falhar.
    """
    validar_tom(tom)
    prompt = _montar_prompt(enriched, tom)
    logger.info(f"Gerando relatório para {enriched.dossier_input.empresa_nome} (tom: {tom})")

    try:
        conteudo, modelo = _chamar_llm(prompt)
    except Exception as e:
        logger.error(f"Falha ao chamar LLM: {e}")
        raise RuntimeError(f"Falha na redação: {e}") from e

    return RedactedDossier(
        enriched=enriched,
        conteudo=conteudo,
        tom_de_voz=tom,
        modelo_usado=modelo,
    )
