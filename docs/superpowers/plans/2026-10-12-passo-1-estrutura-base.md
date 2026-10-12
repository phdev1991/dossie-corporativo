# Passo 1 — Estrutura Base do Projeto + Formato de Entrada do Dossiê

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a estrutura base do Projeto Dossiê Corporativo em Python e definir/implementar o formato de entrada do dossiê corporativo existente.

**Architecture:** Projeto Python com estrutura de pacote (`src/`), entrada do dossiê em JSON validado por Pydantic, e CLI mínima para carregar e validar o dossiê. Subagentes (Passo 2+) consomem o modelo validado; o motor de redação (Passo 3+) consome os dados enriquecidos.

**Tech Stack:** Python 3.11+, Pydantic v2, argparse (stdlib), pytest.

**Spec:** Documentos fornecidos pelo usuário (PRD, TRD, App Flow, UI/UX, Esquema do Backend, Plano de Implementação) — Resumo:
- FR1: Entrada de um dossiê de empresa base (já existente)
- FR2: Execução de subagentes para pesquisa externa (Passo 2+)
- FR3: Módulo de redação comercial (Passo 3+)
- FR4: Skill de output para formato final (Passo 4+)
- Dados: `dossiers` com `id`, `initial_data`, `enriched_data`, `final_output`, `created_at`

## Global Constraints

- Linguagem: Python 3.11+
- Biblioteca de validação: Pydantic v2
- Formato de entrada: JSON estruturado
- Estilo de código: PEP 8, type hints obrigatórias
- Sem dependências externas além de Pydantic e pytest no Passo 1
- Todos os textos de UI/log em português (projeto brasileiro)

## Review Focus

1. **JSON malformado** → deve gerar erro claro (não crash silencioso)
2. **Dossiê com campos obrigatórios ausentes** → deve falhar validação com mensagem legível
3. **Dossiê com campos extras desconhecidos** → deve ser rejeitado ou ignorado (decisão: rejeitar, para garantir contrato rígido)
4. **CLI sem argumentos** → deve mostrar help e sair com código 0
5. **Caminho de arquivo inexistente** → deve gerar erro claro antes de tentar parsear

---

### Task 1: Estrutura de diretórios + configuração do projeto

**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `src/__init__.py`
- Create: `src/schemas/__init__.py`
- Create: `src/models/__init__.py`
- Create: `src/cli/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`

**Interfaces:**
- Consumes: nada (primeira task)
- Produces: estrutura de pacotes Python importável via `from src.schemas import ...`

- [ ] **Step 1: Criar `requirements.txt`**

```
pydantic>=2.5.0
pytest>=8.0.0
```

- [ ] **Step 2: Criar `pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = .
addopts = -v
```

- [ ] **Step 3: Criar os diretórios e arquivos `__init__.py`**

```powershell
New-Item -ItemType Directory -Force src/schemas, src/models, src/cli, tests
New-Item -ItemType File -Force src/__init__.py, src/schemas/__init__.py, src/models/__init__.py, src/cli/__init__.py, tests/__init__.py
```

- [ ] **Step 4: Criar `.gitignore`**

```
__pycache__/
*.pyc
.env
.pytest_cache/
dist/
*.egg-info/
```

- [ ] **Step 5: Verificar que a estrutura existe**

Run: `Get-ChildItem -Recurse src, tests`
Expected: 4 diretórios + 5 arquivos `__init__.py`

---

### Task 2: Modelo Pydantic — `DossierInput` (formato de entrada)

**Files:**
- Create: `src/schemas/dossier_input.py`
- Test: `tests/schemas/test_dossier_input.py`

**Interfaces:**
- Consumes: nada
- Produces:
  - `DossierInput` (Pydantic BaseModel) com campos:
    - `empresa_nome: str` — Nome da empresa (obrigatório)
    - `cnpj: str | None` — CNPJ no formato `00.000.000/0000-00` (opcional)
    - `segmento: str` — Segmento de atuação (obrigatório)
    - `descricao: str` — Descrição da empresa (obrigatório, mínimo 10 caracteres)
    - `dados_financeiros: dict[str, float] | None` — Dados financeiros chave-valor (opcional)
    - `fontes_conhecidas: list[str]` — Fontes já conhecidas (lista, padrão `[]`)
    - `notas_adicionais: str | None` — Notas adicionais do usuário (opcional)
  - Método `to_dict() -> dict` que retorna o modelo como dicionário
  - Validação: `cnpj` deve validar formato (regex `^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$`)

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/schemas/test_dossier_input.py
import pytest
from pydantic import ValidationError
from src.schemas.dossier_input import DossierInput


def test_dossier_input_campos_obrigatorios():
    dossier = DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )
    assert dossier.empresa_nome == "Empresa X"
    assert dossier.segmento == "Tecnologia"


def test_dossier_input_cnpj_valido():
    dossier = DossierInput(
        empresa_nome="Empresa X",
        cnpj="12.345.678/0001-90",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )
    assert dossier.cnpj == "12.345.678/0001-90"


def test_dossier_input_cnpj_invalido():
    with pytest.raises(ValidationError):
        DossierInput(
            empresa_nome="Empresa X",
            cnpj="12345678000190",  # Formato inválido
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
        )


def test_dossier_input_campos_extras_rejeitados():
    with pytest.raises(ValidationError):
        DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
            campo_desconhecido="valor",  # Deve ser rejeitado
        )


def test_dossier_input_descricao_muito_curta():
    with pytest.raises(ValidationError):
        DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Curta",  # Menos de 10 caracteres
        )


def test_dossier_input_to_dict():
    dossier = DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
        dados_financeiros={"receita_anual": 1000000.0},
        fontes_conhecidas=["site.com"],
    )
    result = dossier.to_dict()
    assert isinstance(result, dict)
    assert result["empresa_nome"] == "Empresa X"
    assert result["fontes_conhecidas"] == ["site.com"]
```

- [ ] **Step 2: Rodar o teste para verificar que falha**

Run: `pytest tests/schemas/test_dossier_input.py -v`
Expected: FAIL — "ModuleNotFoundError: No module named 'src.schemas.dossier_input'"

- [ ] **Step 3: Implementar `DossierInput`**

Criar `src/schemas/dossier_input.py` com:

```python
import re
from pydantic import BaseModel, Field, field_validator


class DossierInput(BaseModel):
    model_config = {"extra": "forbid"}

    empresa_nome: str
    cnpj: str | None = None
    segmento: str
    descricao: str = Field(min_length=10)
    dados_financeiros: dict[str, float] | None = None
    fontes_conhecidas: list[str] = Field(default_factory=list)
    notas_adicionais: str | None = None

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", v):
            raise ValueError("CNPJ deve estar no formato 00.000.000/0000-00")
        return v

    def to_dict(self) -> dict:
        return self.model_dump()
```

- [ ] **Step 4: Rodar o teste para verificar que passa**

Run: `pytest tests/schemas/test_dossier_input.py -v`
Expected: PASS (6 passed)

---

### Task 3: Função de carregamento + CLI

**Files:**
- Create: `src/cli/main.py`
- Test: `tests/cli/test_cli.py`
- Create: `data/example_dossier.json`

**Interfaces:**
- Consumes: `DossierInput` de `src.schemas.dossier_input`
- Produces:
  - `carregar_dossier(caminho: str) -> DossierInput` — lê JSON, valida, retorna `DossierInput`
  - CLI: `python -m src.cli.main <caminho_json>` — carrega e imprime resumo do dossiê

- [ ] **Step 1: Criar `data/example_dossier.json`**

```json
{
  "empresa_nome": "TechFlow Solutions",
  "cnpj": "12.345.678/0001-90",
  "segmento": "Tecnologia / Automação",
  "descricao": "Empresa especializada em soluções de automação corporativa e inteligência de dados.",
  "dados_financeiros": {
    "receita_anual": 5000000.0,
    "lucro_liquido": 1200000.0
  },
  "fontes_conhecidas": ["https://techflow.com.br"],
  "notas_adicionais": "Empresa em expansão, foco no mercado B2B."
}
```

- [ ] **Step 2: Escrever testes que falham**

```python
# tests/cli/test_cli.py
import pytest
from src.cli.main import carregar_dossier
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
```

- [ ] **Step 3: Rodar os testes para verificar que falham**

Run: `pytest tests/cli/test_cli.py -v`
Expected: FAIL — "ModuleNotFoundError: No module named 'src.cli.main'"

- [ ] **Step 4: Implementar `src/cli/main.py`**

```python
import argparse
import json
import sys
from pathlib import Path

from src.schemas.dossier_input import DossierInput
from pydantic import ValidationError


def carregar_dossier(caminho: str) -> DossierInput:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Carregar dossiê corporativo")
    parser.add_argument("caminho", help="Caminho do arquivo JSON do dossiê")
    args = parser.parse_args()
    try:
        dossier = carregar_dossier(args.caminho)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Dossiê carregado: {dossier.empresa_nome}")
    print(f"Segmento: {dossier.segmento}")
    print(f"Fontes conhecidas: {len(dossier.fontes_conhecidas)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Rodar os testes para verificar que passam**

Run: `pytest tests/cli/test_cli.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Testar a CLI manualmente**

Run: `python -m src.cli.main data/example_dossier.json`
Expected: saída com "Dossiê carregado: TechFlow Solutions"

---

### Task 4: Testes de integração do Passo 1 + README

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: tudo do Passo 1
- Produces: documentação base para o executor do Passo 2+

- [ ] **Step 1: Rodar todos os testes do Passo 1**

Run: `pytest tests/ -v`
Expected: PASS (10 passed total: 6 do Task 2 + 4 do Task 3)

- [ ] **Step 2: Criar `README.md`**

```markdown
# Projeto Dossiê Corporativo

Sistema inteligente de análise empresarial automatizada.

## Estrutura

```
src/
  schemas/      # Modelos Pydantic e contratos de dados
  models/       # Modelos de dados internos (Passo 2+)
  cli/          # Interface de linha de comando
tests/
data/           # Dossiês de exemplo
```

## Como usar

```bash
pip install -r requirements.txt
python -m src.cli.main data/example_dossier.json
```

## Formato de entrada

O dossiê de entrada é um JSON com os seguintes campos:

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| empresa_nome | str | Sim |
| cnpj | str | Não |
| segmento | str | Sim |
| descricao | str (min 10 chars) | Sim |
| dados_financeiros | dict[str, float] | Não |
| fontes_conhecidas | list[str] | Não |
| notas_adicionais | str | Não |

## Roadmap

- [x] Passo 1 — Estrutura base + formato de entrada
- [ ] Passo 2 — Subagentes de pesquisa externa
- [ ] Passo 3 — Módulo de redação comercial
- [ ] Passo 4 — Skill de output
- [ ] Passo 5 — Integração ponta a ponta
```

- [ ] **Step 3: Verificar estrutura final**

Run: `Get-ChildItem -Recurse src, tests, data`
Expected: todos os arquivos listados no plano existem

---

## Execução do Plano

Este plano está pronto para execução. O usuário já confirmou Python como stack base. **Qual abordagem de execução você prefere?**

- **Subagent-driven** — Um subagente implementa cada task e um reviewer verifica antes do próximo. Mais minucioso, mas mais lento.
- **Native** — Eu implemento todas as tasks nesta sessão, depois um reviewer verifica o resultado final. Mais rápido.

**Recomendação:** para o Passo 1 (tasks pequenas e sequenciais, 4 tasks, ~10 arquivos), **Native** é suficiente. O Passo 2+ (subagentes com lógica complexa) se beneficiaria mais de Subagent-driven.

---

## Handoff para o Passo 2

Após a execução deste plano, o executor do Passo 2 terá disponível:
- `DossierInput` (Pydantic) — modelo validado do dossiê de entrada
- `carregar_dossier(caminho: str) -> DossierInput` — função de carregamento
- Estrutura de pacotes pronta para receber `src/agents/`, `src/tools/`
