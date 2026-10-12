# Passo 3 — Módulo de Redação Comercial

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Desenvolver o módulo de redação comercial que processa os dados enriquecidos e gera a narrativa executiva do relatório com tom de voz corporativo.

**Architecture:** O módulo recebe um `EnrichedDossier` e um perfil de tom de voz, monta um prompt estruturado com template + dados, e usa uma LLM (Claude ou OpenAI) para gerar o texto final. O resultado é um `RedactedDossier` com o texto formatado e metadados da redação.

**Tech Stack:** Python 3.11+, Pydantic v2, anthropic (SDK), openai (SDK), pytest.

**Spec:** Documentos do Projeto Dossiê Corporativo (PRD FR3: "Módulo de redação comercial para estruturar o tom de voz e a formatação corporativa").

## Global Constraints

- Linguagem: Python 3.11+
- SDKs LLM: anthropic (padrão), openai (fallback)
- Formato de saída: Markdown estruturado
- Perfis de tom de voz: formal, consultivo, técnico
- Todos os textos gerados em português
- O módulo NÃO inventa dados — só reda o que está no `EnrichedDossier`

## Review Focus

1. **Dados enriquecidos vazios** → deve gerar relatório com seções "não disponível", não falhar
2. **LLM indisponível** → deve gerar erro claro com mensagem acionável
3. **Prompt muito longo** → deve truncar dados financeiros para caber no contexto
4. **Tom de voz inválido** → deve rejeitar com erro claro
5. **Dados conflitantes** → deve sinalizar no relatório, não escolher arbitrariamente

---

### Task 1: Dependências + configuração LLM

**Files:**
- Modify: `requirements.txt`
- Modify: `config/settings.py`
- Modify: `.env.example`

**Interfaces:**
- Consumes: `Settings` existente
- Produces:
  - `Settings` com novos campos:
    - `anthropic_api_key: str = ""`
    - `openai_api_key: str = ""`
    - `llm_provider: Literal["anthropic", "openai"] = "anthropic"`
    - `redacao_max_tokens: int = 4096`

- [ ] **Step 1: Atualizar `requirements.txt`**

```
pydantic>=2.5.0
pydantic-settings>=2.0.0
pytest>=8.0.0
crewai>=0.80.0
ddgs>=6.0.0
python-dotenv>=1.0.0
anthropic>=0.40.0
openai>=1.0.0
```

- [ ] **Step 2: Atualizar `config/settings.py`**

Adicionar campos:
```python
anthropic_api_key: str = ""
openai_api_key: str = ""
llm_provider: Literal["anthropic", "openai"] = "anthropic"
redacao_max_tokens: int = 4096
```

- [ ] **Step 3: Atualizar `.env.example`**

Adicionar:
```env
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
LLM_PROVIDER=anthropic
REDACAO_MAX_TOKENS=4096
```

- [ ] **Step 4: Verificar importação**

Run: `python -c "from config.settings import settings; print(settings.llm_provider)"`
Expected: `"anthropic"`

---

### Task 2: Modelo `RedactedDossier` (saída da redação)

**Files:**
- Create: `src/models/redacted_dossier.py`
- Test: `tests/models/test_redacted_dossier.py`

**Interfaces:**
- Consumes: `EnrichedDossier`
- Produces:
  - `RedactedDossier` (Pydantic):
    - `enriched: EnrichedDossier`
    - `conteudo: str` — texto Markdown gerado
    - `tom_de_voz: Literal["formal", "consultivo", "tecnico"]`
    - `data_redacao: datetime`
    - `modelo_usado: str`
    - `to_dict() -> dict`

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/models/test_redacted_dossier.py
import pytest
from src.models.redacted_dossier import RedactedDossier
from src.models.enriched_dossier import EnrichedDossier
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def enriched():
    return EnrichedDossier(
        dossier_input=DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
        ),
        dados_pesquisados=[],
    )


def test_redacted_dossier_campos(enriched):
    redacted = RedactedDossier(
        enriched=enriched,
        conteudo="# Relatório\n\nConteúdo do relatório.",
        tom_de_voz="formal",
        modelo_usado="claude-3-5-sonnet",
    )
    assert redacted.tom_de_voz == "formal"
    assert "Relatório" in redacted.conteudo


def test_redacted_dossier_to_dict(enriched):
    redacted = RedactedDossier(
        enriched=enriched,
        conteudo="# Relatório",
        tom_de_voz="consultivo",
        modelo_usado="gpt-4o",
    )
    result = redacted.to_dict()
    assert isinstance(result, dict)
    assert "conteudo" in result
    assert "tom_de_voz" in result
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `pytest tests/models/test_redacted_dossier.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implementar `src/models/redacted_dossier.py`**

```python
"""Modelo do dossiê redigido (relatório final)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.models.enriched_dossier import EnrichedDossier


class RedactedDossier(BaseModel):
    enriched: EnrichedDossier
    conteudo: str
    tom_de_voz: Literal["formal", "consultivo", "tecnico"]
    data_redacao: datetime = Field(default_factory=datetime.now)
    modelo_usado: str

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `pytest tests/models/test_redacted_dossier.py -v`
Expected: PASS (2 passed)

---

### Task 3: Diretrizes de tom de voz

**Files:**
- Create: `src/redacao/tons_de_voz.py`
- Test: `tests/redacao/test_tons_de_voz.py`

**Interfaces:**
- Consumes: nada
- Produces:
  - `TOMS_DE_VOZ: dict[str, dict]` — dicionário com diretrizes por tom
  - `obter_diretrizes(tom: str) -> str` — retorna as diretrizes formatadas para o prompt
  - `validar_tom(tom: str) -> Literal["formal", "consultivo", "tecnico"]` — valida e retorna

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/redacao/test_tons_de_voz.py
import pytest
from src.redacao.tons_de_voz import TOMS_DE_VOZ, obter_diretrizes, validar_tom


def test_tons_de_voz_tem_3_perfis():
    assert set(TOMS_DE_VOZ.keys()) == {"formal", "consultivo", "tecnico"}


def test_obter_diretrizes_retorna_str():
    diretrizes = obter_diretrizes("formal")
    assert isinstance(diretrizes, str)
    assert len(diretrizes) > 0


def test_validar_tom_valido():
    assert validar_tom("formal") == "formal"
    assert validar_tom("consultivo") == "consultivo"
    assert validar_tom("tecnico") == "tecnico"


def test_validar_tom_invalido():
    with pytest.raises(ValueError):
        validar_tom("informal")
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `pytest tests/redacao/test_tons_de_voz.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implementar `src/redacao/tons_de_voz.py`**

```python
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
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `pytest tests/redacao/test_tons_de_voz.py -v`
Expected: PASS (4 passed)

---

### Task 4: Motor de redação (prompt + LLM)

**Files:**
- Create: `src/redacao/motor_redacao.py`
- Test: `tests/redacao/test_motor_redacao.py`

**Interfaces:**
- Consumes: `EnrichedDossier`, `obter_diretrizes`, `settings`
- Produces:
  - `redigir_relatorio(enriched: EnrichedDossier, tom: str = "formal") -> RedactedDossier`
  - `_montar_prompt(enriched: EnrichedDossier, tom: str) -> str` — função interna

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/redacao/test_motor_redacao.py
import pytest
from unittest.mock import patch, MagicMock
from src.redacao.motor_redacao import redigir_relatorio
from src.models.enriched_dossier import EnrichedDossier, DadoPesquisado
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def enriched():
    return EnrichedDossier(
        dossier_input=DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
        ),
        dados_pesquisados=[
            DadoPesquisado(
                categoria="financeiro",
                descricao="Receita anual",
                valor="R$ 5M",
                fontes=[],
            )
        ],
    )


@patch("src.redacao.motor_redacao._chamar_llm")
def test_redigir_relatorio(mock_llm, enriched):
    mock_llm.return_value = "# Relatório Empresa X\n\nConteúdo gerado."
    resultado = redigir_relatorio(enriched, tom="formal")
    assert resultado.tom_de_voz == "formal"
    assert "Relatório" in resultado.conteudo
    assert resultado.modelo_usado


@patch("src.redacao.motor_redacao._chamar_llm")
def test_redigir_relatorio_dados_vazios(mock_llm, enriched):
    enriched.dados_pesquisados = []
    mock_llm.return_value = "# Relatório\n\nSem dados disponíveis."
    resultado = redigir_relatorio(enriched, tom="consultivo")
    assert resultado.tom_de_voz == "consultivo"


def test_redigir_relatorio_tom_invalido(enriched):
    with pytest.raises(ValueError):
        redigir_relatorio(enriched, tom="informal")
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `pytest tests/redacao/test_motor_redacao.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implementar `src/redacao/motor_redacao.py`**

```python
"""Motor de redação comercial: monta prompt e chama LLM."""

import logging

from src.models.enriched_dossier import EnrichedDossier
from src.models.redacted_dossier import RedactedDossier
from src.redacao.tons_de_voz import obter_diretrizes, validar_tom
from config.settings import settings

logger = logging.getLogger(__name__)


def _montar_prompt(enriched: EnrichedDossier, tom: str) -> str:
    """Monta o prompt estruturado para a LLM."""
    d = enriched.dossier_input
    dados = enriched.dados_pesquisados

    secoes_dados = []
    for dado in dados:
        fontes = ", ".join(f.url for f in dado.fontes) or "nenhuma"
        secoes_dados.append(
            f"### {dado.categoria}\n"
            f"- Descrição: {dado.descricao}\n"
            f"- Valor: {dado.valor or 'não informado'}\n"
            f"- Fontes: {fontes}\n"
            f"- Conflito: {'sim' if dado.conflito else 'não'}"
        )

    prompt = f"""Você é um analista corporativo sênior. Redija um dossiê executivo em português.

## Diretrizes de tom de voz
{obter_diretrizes(tom)}

## Dados da empresa
- Nome: {d.empresa_nome}
- CNPJ: {d.cnpj ou 'não informado'}
- Segmento: {d.segmento}
- Descrição: {d.descricao}
- Dados financeiros: {d.dados_financeiros or 'não informados'}
- Notas: {d.notas_adicionais or 'nenhuma'}

## Dados pesquisados externamente
{chr(10).join(secoes_dados) if secoes_dados else 'Nenhum dado externo coletado.'}

## Estrutura do relatório (Markdown)
1. Resumo Executivo
2. Perfil da Empresa
3. Dados Financeiros
4. Panorama de Mercado
5. Concorrentes e Posicionamento
6. Conclusão e Recomendações

Regras:
- NÃO invente dados. Use apenas os dados fornecidos.
- Se uma seção não tiver dados, escreva "Não disponível".
- Marque dados conflitantes com [CONFLITO].
- Use Markdown com headers (##), listas e negrito quando apropriado.
"""
    return prompt


def _chamar_llm(prompt: str) -> tuple[str, str]:
    """Chama a LLM configurada e retorna (resposta, modelo)."""
    if settings.llm_provider == "anthropic":
        return _chamar_anthropic(prompt)
    return _chamar_openai(prompt)


def _chamar_anthropic(prompt: str) -> tuple[str, str]:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=settings.redacao_max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = response.content[0].text
    return texto, "claude-3-5-sonnet-20241022"


def _chamar_openai(prompt: str) -> tuple[str, str]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=settings.redacao_max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = response.choices[0].message.content or ""
    return texto, settings.llm_model


def redigir_relatorio(enriched: EnrichedDossier, tom: str = "formal") -> RedactedDossier:
    """Redige o relatório executivo a partir do dossiê enriquecido.

    Args:
        enriched: Dossiê enriquecido com dados de pesquisa.
        tom: Tom de voz (formal, consultivo, tecnico).

    Returns:
        RedactedDossier com o conteúdo gerado.

    Raises:
        ValueError: Se o tom de voz for inválido.
        RuntimeError: Se a LLM falhar.
    """
    tom_validado = validar_tom(tom)
    prompt = _montar_prompt(enriched, tom_validado)
    logger.info(f"Redigindo relatório para {enriched.dossier_input.empresa_nome} (tom: {tom_validado})")
    try:
        conteudo, modelo = _chamar_llm(prompt)
    except Exception as e:
        logger.error(f"Falha ao chamar LLM: {e}")
        raise RuntimeError(f"Falha na redação: {e}") from e
    return RedactedDossier(
        enriched=enriched,
        conteudo=conteudo,
        tom_de_voz=tom_validado,
        modelo_usado=modelo,
    )
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `pytest tests/redacao/test_motor_redacao.py -v`
Expected: PASS (3 passed)

---

### Task 5: CLI — comando `redigir`

**Files:**
- Modify: `src/cli/main.py`
- Test: `tests/cli/test_redigir.py`

**Interfaces:**
- Consumes: `redigir_relatorio`, `RedactedDossier`
- Produces: CLI `python -m src.cli.main redigir <caminho_enriched> --tom formal -o relatorio.md`

- [ ] **Step 1: Escrever teste que falha**

```python
# tests/cli/test_redigir.py
import json
import pytest
from unittest.mock import patch
from src.cli.main import main
from src.models.redacted_dossier import RedactedDossier
from src.models.enriched_dossier import EnrichedDossier
from src.schemas.dossier_input import DossierInput


@patch("src.cli.main.redigir_relatorio")
def test_cli_redigir(mock_redigir, tmp_path, capsys):
    enriched = EnrichedDossier(
        dossier_input=DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
        ),
        dados_pesquisados=[],
    )
    redacted = RedactedDossier(
        enriched=enriched,
        conteudo="# Relatório\n\nConteúdo.",
        tom_de_voz="formal",
        modelo_usado="claude-3-5-sonnet",
    )
    mock_redigir.return_value = redacted

    enriched_path = tmp_path / "enriched.json"
    enriched_path.write_text(json.dumps(enriched.to_dict(), ensure_ascii=False))

    import sys
    old_argv = sys.argv
    sys.argv = ["main.py", "redigir", str(enriched_path), "--tom", "formal", "-o", str(tmp_path / "relatorio.md")]
    try:
        main()
    finally:
        sys.argv = old_argv

    output = tmp_path / "relatorio.md"
    assert output.exists()
    assert "Relatório" in output.read_text(encoding="utf-8")
```

- [ ] **Step 2: Rodar teste para verificar que falha**

Run: `pytest tests/cli/test_redigir.py -v`
Expected: FAIL

- [ ] **Step 3: Adicionar comando `redigir` à CLI**

Adicionar ao `main()`:
```python
parser_redigir = subparsers.add_parser("redigir", help="Redigir relatório executivo")
parser_redigir.add_argument("caminho", help="Caminho do JSON enriquecido")
parser_redigir.add_argument("--tom", choices=["formal", "consultivo", "tecnico"], default="formal")
parser_redigir.add_argument("--output", "-o", help="Caminho do arquivo de saída (.md)")
parser_redigir.set_defaults(func=cmd_redigir)
```

E a função:
```python
def cmd_redigir(args: argparse.Namespace) -> None:
    from src.redacao.motor_redacao import redigir_relatorio
    from src.models.enriched_dossier import EnrichedDossier

    data = json.loads(Path(args.caminho).read_text(encoding="utf-8"))
    enriched = EnrichedDossier(**data)
    redacted = redigir_relatorio(enriched, tom=args.tom)
    output = args.output or "data/relatorio.md"
    Path(output).write_text(redacted.conteudo, encoding="utf-8")
    print(f"Relatório salvo em: {output}")
```

- [ ] **Step 4: Rodar teste para verificar que passa**

Run: `pytest tests/cli/test_redigir.py -v`
Expected: PASS

---

### Task 6: Integração + documentação

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: tudo do Passo 3
- Produces: documentação atualizada

- [ ] **Step 1: Rodar todos os testes**

Run: `pytest tests/ -v`
Expected: PASS (todos os testes do Passo 1 + 2 + 3)

- [ ] **Step 2: Atualizar `README.md`**

Adicionar seção sobre o Passo 3:

```markdown
## Redação comercial

```bash
python -m src.cli.main redigir data/enriched.json --tom formal -o data/relatorio.md
```

### Tons de voz disponíveis

- `formal` — linguagem corporativa tradicional
- `consultivo` — tom de consultor, orientado a recomendações
- `tecnico` — linguagem técnica especializada
```

---

## Execução do Plano

**Qual abordagem de execução você prefere?**

- **Subagent-driven** — um subagente implementa cada task, um reviewer verifica antes do próximo.
- **Native** — eu implemento todas as tasks nesta sessão, depois um reviewer final.

**Recomendação:** para o Passo 3, **Native** é suficiente — as tasks são pequenas e o motor de redação é isolado.
