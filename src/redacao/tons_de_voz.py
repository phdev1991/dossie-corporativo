"""Diretrizes de tom de voz para a redação comercial."""

from typing import Literal

TOMS_DE_VOZ: dict[str, dict] = {
    "formal": {
        "descricao": "Linguagem corporativa tradicional, impessoal e respeitosa",
        "diretrizes": [
            "Use terceira pessoa do plural ou impessoal",
            "Evite gírias e coloquialismos",
            "Prefira construções gramaticais completas",
            "Use vocabulário técnico apropriado",
        ],
    },
    "consultivo": {
        "descricao": "Tom de consultor: direto, orientado a recomendações",
        "diretrizes": [
            "Use segunda pessoa do plural (vocês) quando apropriado",
            "Estruture como recomendações acionáveis",
            "Seja direto e objetivo",
            "Use dados para suportar afirmações",
        ],
    },
    "tecnico": {
        "descricao": "Linguagem técnica especializada para audiência técnica",
        "diretrizes": [
            "Use terminologia técnica precisa",
            "Inclua métricas e dados quantitativos",
            "Estruture de forma lógica e sistemática",
            "Assuma conhecimento técnico do leitor",
        ],
    },
}


def obter_diretrizes(tom: str) -> str:
    """Retorna as diretrizes formatadas para inclusão no prompt."""
    if tom not in TOMS_DE_VOZ:
        raise ValueError(f"Tom de voz inválido: {tom}. Opções: {list(TOMS_DE_VOZ.keys())}")
    info = TOMS_DE_VOZ[tom]
    linhas = [f"Tom: {info['descricao']}"]
    linhas.extend(f"- {d}" for d in info["diretrizes"])
    return "\n".join(linhas)


def validar_tom(tom: str) -> Literal["formal", "consultivo", "tecnico"]:
    """Valida e retorna o tom de voz."""
    if tom not in TOMS_DE_VOZ:
        raise ValueError(f"Tom de voz inválido: {tom}. Opções: {list(TOMS_DE_VOZ.keys())}")
    return tom  # type: ignore
