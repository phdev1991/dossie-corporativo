# Dossiê Corporativo

Sistema inteligente de análise empresarial automatizada. A partir de um dossiê de entrada (JSON), o sistema pesquisa dados externos na web, enriquece o dossiê e redige um relatório executivo com agentes de IA.

## Como funciona

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Dossiê         │     │  Pesquisa        │     │  Redação        │     │  Output      │
│  (JSON)         │────▶│  (Web Search)    │────▶│  (LLM)          │────▶│  (MD / HTML) │
│                 │     │                  │     │                 │     │              │
│ Dados da        │     │ Subagentes       │     │ Motor de        │     │ Relatório    │
│ empresa        │     │ CrewAI + DDG     │     │ redação com     │     │ executivo    │
│                 │     │                  │     │ tons de voz     │     │ formatado    │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
```

### Fluxo em 3 fases

1. **Pesquisa** — Subagentes CrewAI buscam dados externos (mercado, financeiro, concorrência) usando DuckDuckGo Search
2. **Redação** — Motor de redação monta um prompt com os dados enriquecidos e chama um LLM (Anthropic Claude ou OpenAI GPT) para gerar o relatório executivo
3. **Output** — Skill de output formata o relatório em Markdown ou HTML com header, meta e footer

## Instalação

```bash
git clone https://github.com/phdev1991/dossie-corporativo.git
cd dossie-corporativo
pip install -r requirements.txt
cp .env.example .env
```

## Configuração

Edite o arquivo `.env` com suas chaves de API:

```env
# Obrigatório: pelo menos uma chave
ANTHROPIC_API_KEY=sua_chave_anthropic_aqui
OPENAI_API_KEY=sua_chave_openai_aqui

# Provedor LLM: anthropic (padrão) ou openai
LLM_PROVIDER=anthropic

# Modelo LLM
LLM_MODEL=gpt-4o-mini

# Redação
REDACAO_MAX_TOKENS=4096

# Busca web
SEARCH_MAX_RESULTS=5
SEARCH_TIMEOUT=30

# Logs
LOG_LEVEL=INFO
```

## Uso

### Pipeline completo (um comando)

```bash
python -m src.cli.main pipeline data/example_dossier.json --tom consultivo --formato markdown
```

### Por etapas

```bash
# 1. Carregar e validar o dossiê
python -m src.cli.main carregar data/example_dossier.json

# 2. Pesquisar dados externos
python -m src.cli.main pesquisar data/example_dossier.json -o data/enriched.json

# 3. Redigir relatório executivo
python -m src.cli.main redigir data/enriched.json --tom formal --formato markdown -o data/relatorio.md
```

### Tons de voz

| Tom | Descrição |
|-----|-----------|
| `formal` | Linguagem corporativa tradicional |
| `consultivo` | Tom de consultor, orientado a recomendações |
| `tecnico` | Linguagem técnica especializada |

### Formatos de saída

- `markdown` — arquivo `.md` com header, meta e footer
- `html` — documento HTML completo

## Formato de entrada

O dossiê de entrada é um JSON:

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

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| `empresa_nome` | string | Sim |
| `cnpj` | string | Não |
| `segmento` | string | Sim |
| `descricao` | string (mín. 10 caracteres) | Sim |
| `dados_financeiros` | dict[string, float] | Não |
| `fontes_conhecidas` | list[string] | Não |
| `notas_adicionais` | string | Não |

## Exemplo de saída

Veja o [relatório de exemplo](data/relatorio_exemplo.md) gerado para a TechFlow Solutions.

## Estrutura do projeto

```
src/
  schemas/      # Modelos Pydantic e contratos de dados
  models/       # Modelos internos (EnrichedDossier, RedactedDossier)
  agents/       # Subagentes de pesquisa (CrewAI)
  tools/        # Ferramentas (busca web com DuckDuckGo)
  redacao/      # Motor de redação comercial + tons de voz
  output/       # Skill de output (formatação Markdown/HTML)
  cli/          # Interface de linha de comando
  pipeline.py   # Pipeline de integração ponta a ponta
config/         # Configurações (Settings via pydantic-settings)
tests/          # Suíte de testes (47 testes)
data/           # Dossiês e relatórios de exemplo
```

## Testes

```bash
python -m pytest tests/ -v
```

## Stack

- **Python 3.12** — linguagem principal
- **Pydantic v2** — validação de dados e contratos rígidos
- **CrewAI** — orquestração de subagentes de pesquisa
- **DuckDuckGo Search (ddgs)** — busca web gratuita
- **Anthropic Claude** — LLM padrão para redação
- **OpenAI GPT** — LLM fallback
- **pytest** — testes

## Licença

MIT
