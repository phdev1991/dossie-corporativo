"""Skill de output — formata a saída final do dossiê corporativo."""

import logging
from pathlib import Path
from typing import Literal

from src.models.redacted_dossier import RedactedDossier

logger = logging.getLogger(__name__)


def formatar_relatorio_markdown(redacted: RedactedDossier) -> str:
    """Formata o relatório final em Markdown padronizado.

    Args:
        redacted: Dossiê redigido com conteúdo gerado.

    Returns:
        String com o relatório formatado em Markdown.
    """
    d = redacted.enriched.dossier_input
    data = redacted.data_redacao.strftime("%d/%m/%Y %H:%M")

    header = f"""# Dossiê Corporativo — {d.empresa_nome}

**Segmento:** {d.segmento}
**Data:** {data}
**Tom de voz:** {redacted.tom_de_voz}
**Modelo:** {redacted.modelo_usado}

---

"""

    footer = f"""

---

*Relatório gerado automaticamente pelo Projeto Dossiê Corporativo.*
*Total de fontes consultadas: {redacted.enriched.total_fontes}*
"""

    return header + redacted.conteudo + footer


def formatar_relatorio_html(redacted: RedactedDossier) -> str:
    """Formata o relatório final em HTML padronizado.

    Args:
        redacted: Dossiê redigido com conteúdo gerado.

    Returns:
        String com o relatório formatado em HTML.
    """
    d = redacted.enriched.dossier_input
    data = redacted.data_redacao.strftime("%d/%m/%Y %H:%M")

    conteudo_html = (
        redacted.conteudo.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    conteudo_html = conteudo_html.replace("\n\n", "</p><p>")
    conteudo_html = conteudo_html.replace("\n", "<br>")
    conteudo_html = f"<p>{conteudo_html}</p>"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Dossiê Corporativo — {d.empresa_nome}</title>
</head>
<body>
    <h1>Dossiê Corporativo — {d.empresa_nome}</h1>
    <p><strong>Segmento:</strong> {d.segmento}<br>
    <strong>Data:</strong> {data}<br>
    <strong>Tom de voz:</strong> {redacted.tom_de_voz}<br>
    <strong>Modelo:</strong> {redacted.modelo_usado}</p>
    {conteudo_html}
    <hr>
    <p><em>Relatório gerado automaticamente. Fontes consultadas: {redacted.enriched.total_fontes}</em></p>
</body>
</html>"""


def salvar_relatorio(
    redacted: RedactedDossier,
    caminho: str,
    formato: Literal["markdown", "html"] = "markdown",
) -> str:
    """Salva o relatório formatado em arquivo.

    Args:
        redacted: Dossiê redigido.
        caminho: Caminho do arquivo de saída.
        formato: Formato de saída (markdown ou html).

    Returns:
        Caminho do arquivo salvo.

    Raises:
        ValueError: Se o formato não for suportado.
    """
    if formato == "markdown":
        conteudo = formatar_relatorio_markdown(redacted)
        if not caminho.endswith(".md"):
            caminho += ".md"
    elif formato == "html":
        conteudo = formatar_relatorio_html(redacted)
        if not caminho.endswith(".html"):
            caminho += ".html"
    else:
        raise ValueError(f"Formato não suportado: {formato}")

    Path(caminho).write_text(conteudo, encoding="utf-8")
    logger.info(f"Relatório salvo em: {caminho}")
    return caminho
