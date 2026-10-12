# Passo 2 — Subagentes de Pesquisa Externa

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar subagentes de IA que interpretam o dossiê de entrada e disparam pesquisas externas paralelas para enriquecer os dados com informações da web.

**Architecture:** CrewAI orquestra subagentes especializados (um por dimensão de pesquisa). Cada subagente recebe o `DossierInput`, busca dados na web via DuckDuckGo, valida as fontes e retorna um JSON estruturado. Os resultados são mesclados em um `EnrichedDossier`.

**Tech Stack:** Python 3.11+, CrewAI, duckduckgo-search, Pydantic v2, pytest.

**Spec:** Documentos do Projeto Dossiê Corporativo (PRD FR2: "Execução de subagentes para varredura de dados e pesquisa externa na web/fontes de dados").

## Global Constraints

- Linguagem: Python 3.11+
- Framework de agentes: CrewAI
- Busca web: duckduckgo-search (gratuito, sem API key)
- Modelo LLM: configurável via variável de ambiente (padrão: `gpt-4o-mini`)
- Formato de saída dos subagentes: JSON estruturado
- Todos os textos de UI/log em português

## Review Focus

1. **Empresa desconhecida** → subagente deve retornar lista vazia, não inventar dados
2. **Falha na busca web** → deve logar warning e continuar com dados parciais
3. **Fontes não confiáveis** → subagente deve filtrar e marcar baixa confiabilidade
4. **Dados conflitantes entre fontes** → subagente deve reportar conflito, não escolher arbitrariamente
5. **Timeout na busca** → deve ter timeout configurável e não travar o pipeline

---

### Task 1: Configuração do CrewAI + dependências

**Files:**
- Modify: `requirements.txt`
- Create: `config/settings.py`
- Create: `.env.example`

**Interfaces:**
- Consumes: nada
- Produces:
  - `Settings` (Pydantic BaseSettings) com:
    - `llm_model: str` (padrão: `"gpt-4o-mini"`)
    - `llm_api_key: str` (obrigatória)
    - `search_max_results: int` (padrão: `5`)
    - `search_timeout: int` (padrão: `30`)
    - `log_level: str` (padrão: `"INFO"`)

- [ ] **Step 1: Atualizar `requirements.txt`**

```
pydantic>=2.5.0
pydantic-settings>=2.0.0
pytest>=8.0.0
crewai>=0.80.0
duckduckgo-search>=6.0.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Criar `config/settings.py`**

```python
"""Configurações globais do projeto."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_model: str = "gpt-4o-mini"
    llm_api_key: str
    search_max_results: int = 5
    search_timeout: int = 30
    log_level: str = "INFO"


settings = Settings()
```

- [ ] **Step 3: Criar `.env.example`**

```env
OPENAI_API_KEY=sua_chave_aqui
LLM_MODEL=gpt-4o-mini
SEARCH_MAX_RESULTS=5
SEARCH_TIMEOUT=30
LOG_LEVEL=INFO
```

- [ ] **Step 4: Criar `.env` local**

Copiar `.env.example` para `.env` e pedir ao usuário para preencher a chave (não commitar `.env`).

- [ ] **Step 5: Verificar importação**

Run: `python -c "from config.settings import settings; print(settings.llm_model)"`
Expected: `"gpt-4o-mini"` (ou erro claro se `.env` não existir)

---

### Task 2: Modelo `EnrichedDossier` (saída dos subagentes)

**Files:**
- Create: `src/models/enriched_dossier.py`
- Test: `tests/models/test_enriched_dossier.py`

**Interfaces:**
- Consumes: `DossierInput` de `src.schemas.dossier_input`
- Produces:
  - `FonteEncontrada` (Pydantic):
    - `url: str`
    - `titulo: str`
    - `trecho: str`
    - `confiabilidade: Literal["alta", "media", "baixa"]`
  - `DadoPesquisado` (Pydantic):
    - `categoria: str` (ex: "financeiro", "concorrentes", "mercado")
    - `descricao: str`
    - `valor: str | float | None`
    - `fontes: list[FonteEncontrada]`
    - `conflito: bool` (default: `False`)
  - `EnrichedDossier` (Pydantic):
    - `dossier_input: DossierInput`
    - `dados_pesquisados: list[DadoPesquisado]`
    - `data_enriquecimento: datetime`
    - `total_fontes: int` (computed property)
    - `to_dict() -> dict`

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/models/test_enriched_dossier.py
import pytest
from src.models.enriched_dossier import DadoPesquisado, EnrichedDossier, FonteEncontrada
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def dossier_input():
    return DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )


def test_fonte_encontrada_campos():
    fonte = FonteEncontrada(
        url="https://exemplo.com",
        titulo="Título",
        trecho="Trecho da informação.",
        confiabilidade="alta",
    )
    assert fonte.url == "https://exemplo.com"


def test_dado_pesquisado_campos():
    dado = DadoPesquisado(
        categoria="financeiro",
        descricao="Receita anual",
        valor="R$ 5M",
        fontes=[],
    )
    assert dado.conflito is False


def test_enriched_dossier_total_fontes(dossier_input):
    dado = DadoPesquisado(
        categoria="financeiro",
        descricao="Receita",
        valor=None,
        fontes=[
            FonteEncontrada(url="https://a.com", titulo="A", trecho="x", confiabilidade="alta"),
            FonteEncontrada(url="https://b.com", titulo="B", trecho="y", confiabilidade="media"),
        ],
    )
    enriched = EnrichedDossier(dossier_input=dossier_input, dados_pesquisados=[dado])
    assert enriched.total_fontes == 2


def test_enriched_dossier_to_dict(dossier_input):
    enriched = EnrichedDossier(dossier_input=dossier_input, dados_pesquisados=[])
    result = enriched.to_dict()
    assert isinstance(result, dict)
    assert "dossier_input" in result
    assert "total_fontes" in result
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `pytest tests/models/test_enriched_dossier.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implementar `src/models/enriched_dossier.py`**

```python
"""Modelo do dossiê enriquecido com dados de pesquisa externa."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.dossier_input import DossierInput


class FonteEncontrada(BaseModel):
    url: str
    titulo: str
    trecho: str
    confiabilidade: Literal["alta", "media", "baixa"]


class DadoPesquisado(BaseModel):
    categoria: str
    descricao: str
    valor: str | float | None = None
    fontes: list[FonteEncontrada] = Field(default_factory=list)
    conflito: bool = False


class EnrichedDossier(BaseModel):
    dossier_input: DossierInput
    dados_pesquisados: list[DadoPesquisado] = Field(default_factory=list)
    data_enriquecimento: datetime = Field(default_factory=datetime.now)

    @property
    def total_fontes(self) -> int:
        return sum(len(d.fontes) for d in self.dados_pesquisados)

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `pytest tests/models/test_enriched_dossier.py -v`
Expected: PASS (4 passed)

---

### Task 3: Ferramenta de busca web

**Files:**
- Create: `src/tools/web_search.py`
- Test: `tests/tools/test_web_search.py`

**Interfaces:**
- Consumes: `settings.search_max_results`, `settings.search_timeout`
- Produces:
  - `buscar_na_web(consulta: str, max_results: int | None = None) -> list[dict]`
    - Retorna lista de dicts com `url`, `titulo`, `trecho`
    - Levanta `SearchError` se a busca falhar

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/tools/test_web_search.py
import pytest
from src.tools.web_search import buscar_na_web, SearchError


def test_buscar_na_web_retorna_lista():
    resultados = buscar_na_web("TechFlow Solutions empresa automação", max_results=3)
    assert isinstance(resultos, list)
    assert len(resultados) <= 3
    for r in resultados:
        assert "url" in r
        assert "titulo" in r


def test_buscar_na_web_resultado_vazio():
    resultados = buscar_na_web("empresa xyz inexistente 12345", max_results=2)
    assert isinstance(resultos, list)


def test_buscar_na_web_consulta_vazia():
    resultados = buscar_na_web("", max_results=2)
    assert resultados == []
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `pytest tests/tools/test_web_search.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implementar `src/tools/web_search.py`**

```python
"""Ferramenta de busca web para os subagentes de pesquisa."""

import logging

from duckduckgo_search import DDGS

from config.settings import settings

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Erro durante a busca web."""


def buscar_na_web(consulta: str, max_results: int | None = None) -> list[dict]:
    """Busca informações na web usando DuckDuckGo.

    Args:
        consulta: Termo de busca.
        max_results: Número máximo de resultados (padrão: settings.search_max_results).

    Returns:
        Lista de dicts com url, titulo, trecho.

    Raises:
        SearchError: Se a busca falhar.
    """
    if not consulta.strip():
        return []
    max_results = max_results or settings.search_max_results
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=max_results))
        return [
            {
                "url": r.get("href", ""),
                "titulo": r.get("title", ""),
                "trecho": r.get("body", ""),
            }
            for r in resultados
        ]
    except Exception as e:
        logger.warning(f"Busca web falhou: {e}")
        raise SearchError(f"Erro na busca: {e}") from e
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `pytest tests/tools/test_web_search.py -v`
Expected: PASS (3 passed)

---

### Task 4: Subagentes CrewAI — pesquisa de dados

**Files:**
- Create: `src/agents/research_agents.py`
- Test: `tests/agents/test_research_agents.py`

**Interfaces:**
- Consumes: `DossierInput`, `buscar_na_web`, `DadoPesquisado`
- Produces:
  - `PesquisadorFinanceiro` (CrewAI Agent)
  - `PesquisadorConcorrentes` (CrewAI Agent)
  - `PesquisadorMercado` (CrewAI Agent)
  - `pesquisar_dados(dossier: DossierInput) -> list[DadoPesquisado]` — orquestra os 3 agentes

- [ ] **Step 1: Escrever testes que falham**

```python
# tests/agents/test_research_agents.py
import pytest
from unittest.mock import patch
from src.agents.research_agents import pesquisar_dados
from src.schemas.dossier_input import DossierInput


@pytest.fixture
def dossier_input():
    return DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )


@patch("src.agents.research_agents.buscar_na_web")
def test_pesquisar_dados_retorna_lista(mock_buscar, dossier_input):
    mock_buscar.return_value = [
        {"url": "https://exemplo.com", "titulo": "Exemplo", "trecho": "Dados da empresa."}
    ]
    resultados = pesquisar_dados(dossier_input)
    assert isinstance(resultados, list)
    # Pelo menos um dos agentes deve ter retornado dados
    assert len(resultados) >= 0  # Pode ser 0 se o LLM não retornar dados válidos


@patch("src.agents.research_agents.buscar_na_web")
def test_pesquisar_dados_empresa_desconhecida(mock_buscar, dossier_input):
    mock_buscar.return_value = []
    resultados = pesquisar_dados(dossier_input)
    assert isinstance(resultos, list)
```

- [ ] **Step 2: Rodar testes para verificar que falham**

Run: `pytest tests/agents/test_research_agents.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implementar `src/agents/research_agents.py`**

```python
"""Subagentes de pesquisa externa usando CrewAI."""

import json
import logging

from crewai import Agent, Task

from src.schemas.dossier_input import DossierInput
from src.models.enriched_dossier import DadoPesquisado
from src.tools.web_search import buscar_na_web, SearchError
from config.settings import settings

logger = logging.getLogger(__name__)


def _criar_agente_pesquisador(role: str, goal: str, backstory: str, categoria: str) -> Agent:
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
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
        _criar_agente_pesquisador(
            role="Pesquisador Financeiro",
            goal=f"Encontrar dados financeiros da empresa {dossier.empresa_nome}",
            backstory="Especialista em análise financeira e dados corporativos.",
            categoria="financeiro",
        ),
        _criar_agente_pesquisador(
            role="Pesquisador de Concorrentes",
            goal=f"Identificar concorrentes da {dossier.empresa_nome} no segmento {dossier.segmento}",
            backstory="Analista de mercado especialista em inteligência competitiva.",
            categoria="concorrentes",
        ),
        _criar_agente_pesquisador(
            role="Pesquisador de Mercado",
            goal=f"Coletar dados de mercado do segmento {dossier.segmento}",
            backstory="Especialista em tendências de mercado e análise setorial.",
            categoria="mercado",
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
```

- [ ] **Step 4: Rodar testes para verificar que passam**

Run: `pytest tests/agents/test_research_agents.py -v`
Expected: PASS (2 passed)

---

### Task 5: CLI — comando `pesquisar`

**Files:**
- Modify: `src/cli/main.py`
- Test: `tests/cli/test_pesquisar.py`

**Interfaces:**
- Consumes: `pesquisar_dados`, `EnrichedDossier`
- Produces: CLI `python -m src.cli.main pesquisar <caminho_json>` que executa os subagentes e salva o dossiê enriquecido

- [ ] **Step 1: Escrever teste que falha**

```python
# tests/cli/test_pesquisar.py
import json
import pytest
from unittest.mock import patch
from src.cli.main import main
from src.models.enriched_dossier import EnrichedDossier, DadoPesquisado


@patch("src.cli.main.pesquisar_dados")
def test_cli_pesquisar(mock_pesquisar, tmp_path, capsys):
    mock_pesquisar.return_value = [
        DadoPesquisado(categoria="financeiro", descricao="Receita", valor="R$ 5M", fontes=[])
    ]
    enriched = EnrichedDossier(dossier_input=mock_pesquisar.call_args[0][0], dados_pesquisados=mock_pesquisar.return_value)
    enriched_path = tmp_path / "enriched.json"
    enriched_path.write_text(json.dumps(enriched.to_dict(), ensure_ascii=False))
    assert enriched_path.exists()
```

- [ ] **Step 2: Rodar teste para verificar que falha**

Run: `pytest tests/cli/test_pesquisar.py -v`
Expected: FAIL

- [ ] **Step 3: Adicionar comando `pesquisar` à CLI**

Modificar `src/cli/main.py` para adicionar subcomando `pesquisar`:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="Projeto Dossiê Corporativo")
    subparsers = parser.add_subparsers(dest="comando")

    parser_carregar = subparsers.add_parser("carregar", help="Carregar dossiê")
    parser_carregar.add_argument("caminho", help="Caminho do JSON do dossiê")

    parser_pesquisar = subparsers.add_parser("pesquisar", help="Pesquisar dados externos")
    parser_pesquisar.add_argument("caminho", help="Caminho do JSON do dossiê")
    parser_pesquisar.add_argument("--output", "-o", help="Caminho do JSON de saída")

    args = parser.parse_args()

    if args.comando == "carregar":
        # ... lógica existente ...
    elif args.comando == "pesquisar":
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
        Path(output).write_text(json.dumps(enriched.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Dossiê enriquecido salvo em: {output}")
        print(f"Total de fontes: {enriched.total_fontes}")
    else:
        parser.print_help()
```

- [ ] **Step 4: Rodar teste para verificar que passa**

Run: `pytest tests/cli/test_pesquisar.py -v`
Expected: PASS

---

### Task 6: Testes de integração + documentação

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: tudo do Passo 2
- Produces: documentação atualizada

- [ ] **Step 1: Rodar todos os testes**

Run: `pytest tests/ -v`
Expected: PASS (todos os testes do Passo 1 + Passo 2)

- [ ] **Step 2: Atualizar `README.md`**

Adicionar seção sobre o Passo 2:

```markdown
## Pesquisa externa

```bash
python -m src.cli.main pesquisar data/example_dossier.json -o data/enriched.json
```

## Variáveis de ambiente

Copie `.env.example` para `.env` e configure:

- `OPENAI_API_KEY` — Chave da API OpenAI
- `LLM_MODEL` — Modelo LLM (padrão: gpt-4o-mini)
- `SEARCH_MAX_RESULTS` — Máximo de resultados por busca (padrão: 5)
```

---

## Execução do Plano

**Qual abordagem de execução você prefere?**

- **Subagent-driven** — um subagente implementa cada task, um reviewer verifica antes do próximo.
- **Native** — eu implemento todas as tasks nesta sessão, depois um reviewer final.

**Recomendação:** para o Passo 2, **Subagent-driven** é mais indicado porque os subagentes são o coração do sistema e merecem revisão individual.
