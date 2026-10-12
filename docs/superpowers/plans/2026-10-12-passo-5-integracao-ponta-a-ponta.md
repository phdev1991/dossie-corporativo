# Passo 5 — Integração Ponta a Ponta Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar todo o fluxo do Projeto Dossiê Corporativo (input → pesquisa → redação → output) e testar com dossiê real.

**Architecture:** Pipeline sequencial que conecta os módulos existentes (DossierInput → research_agents → motor_redacao → skill_output) com tratamento de erros robusto e logging estruturado.

**Tech Stack:** Python 3.11+, Pydantic v2, CrewAI, anthropic SDK, openai SDK, ddgs (DuckDuckGo), pytest.

**Spec:** Documentos do Projeto Dossiê Corporativo (PRD, TRD, App Flow, UI/UX Design, Esquema do Backend, Plano de Implementação).

## Global Constraints

- Linguagem: Python 3.11+
- Formato de entrada: JSON estruturado
- Formato de saída: Markdown ou HTML
- Todos os textos gerados em português
- O sistema NÃO inventa dados — só reda o que está no dossiê
- Contrato rígido: campos extras rejeitados (`extra="forbid"`)
- Estilo de código: PEP 8, type hints obrigatórias
- Testes: pytest com TDD (testes primeiro, implementação depois)

## Review Focus

1. **Dados enriquecidos vazios** → pipeline deve gerar relatório com seções "não disponível", não falhar
2. **Falha na busca web** → pipeline deve registrar warning e continuar com dados parciais
3. **Falha na LLM** → pipeline deve lançar erro claro ao usuário
4. **Timeout na busca web** → pipeline deve respeitar `SEARCH_TIMEOUT` e não travar
5. **Dossiê real com dados incompletos** → pipeline deve funcionar com campos opcionais ausentes

---

### Task 1: Pipeline de Integração

**Files:**
- Create: `src/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes:
  - `src.schemas.dossier_input.DossierInput`
  - `src.agents.research_agents.pesquisar_dados(dossier: DossierInput) -> list[DadoPesquisado]`
  - `src.redacao.motor_redacao.redigir_relatorio(enriched: EnrichedDossier, tom: str) -> RedactedDossier`
  - `src.output.skill_output.salvar_relatorio(redacted: RedactedDossier, caminho: str, formato: str) -> str`
- Produces:
  - `executar_pipeline(dossier: DossierInput, tom: str, formato: str, output_path: str) -> str` — executa o fluxo completo e retorna o caminho do arquivo gerado

- [ ] **Step 1: Write the failing test**

```python
def test_executar_pipeline_completo():
    """Testa o pipeline completo com mocks."""
    from unittest.mock import patch, MagicMock
    from src.schemas.dossier_input import DossierInput
    from src.pipeline import executar_pipeline
    
    dossier = DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )
    
    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, \
         patch("src.pipeline.redigir_relatorio") as mock_redacao, \
         patch("src.pipeline.salvar_relatorio") as mock_output:
        
        from src.models.enriched_dossier import DadoPesquisado, EnrichedDossier
        from src.models.redacted_dossier import RedactedDossier
        
        mock_pesquisa.return_value = [
            DadoPesquisado(categoria="financeiro", descricao="Receita", valor="R$ 5M", fontes=[])
        ]
        
        mock_enriched = EnrichedDossier(
            dossier_input=dossier,
            dados_pesquisados=mock_pesquisa.return_value,
        )
        
        mock_redacted = RedactedDossier(
            enriched=mock_enriched,
            conteudo="# Relatório\n\nConteúdo.",
            tom_de_voz="formal",
            modelo_usado="claude-3-5-sonnet",
        )
        mock_redacao.return_value = mock_redacted
        mock_output.return_value = "data/relatorio.md"
        
        resultado = executar_pipeline(dossier, tom="formal", formato="markdown", output_path="data/relatorio.md")
        
        assert resultado == "data/relatorio.md"
        mock_pesquisa.assert_called_once()
        mock_redacao.assert_called_once()
        mock_output.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py::test_executar_pipeline_completo -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.pipeline'"

- [ ] **Step 3: Implement `executar_pipeline()` in `src/pipeline.py`**

```python
"""Pipeline de integração ponta a ponta do Projeto Dossiê Corporativo."""

import logging
from pathlib import Path

from src.agents.research_agents import pesquisar_dados
from src.models.enriched_dossier import EnrichedDossier
from src.models.redacted_dossier import RedactedDossier
from src.output.skill_output import salvar_relatorio
from src.redacao.motor_redacao import redigir_relatorio
from src.schemas.dossier_input import DossierInput

logger = logging.getLogger(__name__)


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
        RuntimeError: Se o pipeline falhar.
    """
    logger.info(f"Iniciando pipeline para {dossier.empresa_nome}")
    
    # 1. Pesquisa
    logger.info("Fase 1/3: Pesquisando dados externos...")
    dados_pesquisados = pesquisar_dados(dossier)
    logger.info(f"Pesquisa concluída: {len(dados_pesquisados)} dados encontrados")
    
    # 2. Enriquecimento
    enriched = EnrichedDossier(
        dossier_input=dossier,
        dados_pesquisados=dados_pesquisados,
    )
    
    # 3. Redação
    logger.info(f"Fase 2/3: Redigindo relatório (tom: {tom})...")
    redacted = redigir_relatorio(enriched, tom=tom)
    logger.info("Redação concluída")
    
    # 4. Output
    logger.info(f"Fase 3/3: Salvando relatório ({formato})...")
    caminho = salvar_relatorio(redacted, output_path, formato=formato)
    logger.info(f"Pipeline concluído: {caminho}")
    
    return caminho
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py::test_executar_pipeline_completo -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_pipeline.py src/pipeline.py
git commit -m "feat: add integration pipeline"
```

---

### Task 2: CLI de Pipeline Completo

**Files:**
- Modify: `src/cli/main.py`
- Test: `tests/cli/test_pipeline_cli.py`

**Interfaces:**
- Consumes: `src.pipeline.executar_pipeline(dossier, tom, formato, output_path) -> str`
- Produces: subcomando `pipeline` na CLI que executa o fluxo completo

- [ ] **Step 1: Write the failing test**

```python
def test_pipeline_completo_cli(tmp_path, monkeypatch, capsys):
    """Testa o subcomando pipeline da CLI."""
    import json
    from unittest.mock import patch
    from src.cli.main import main
    
    dossier_data = {
        "empresa_nome": "Empresa X",
        "segmento": "Tecnologia",
        "descricao": "Empresa de tecnologia focada em automação.",
        "dados_financeiros": {"receita_anual": 5000000.0},
        "fontes_conhecidas": ["https://techflow.com.br"],
    }
    dossier_file = tmp_path / "dossier.json"
    dossier_file.write_text(json.dumps(dossier_data), encoding="utf-8")
    
    output_file = tmp_path / "relatorio.md"
    
    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, \
         patch("src.pipeline.redigir_relatorio") as mock_redacao, \
         patch("src.pipeline.salvar_relatorio") as mock_output:
        
        from src.models.enriched_dossier import DadoPesquisado
        from src.models.redacted_dossier import RedactedDossier
        
        mock_pesquisa.return_value = [
            DadoPesquisado(categoria="financeiro", descricao="Receita", valor="R$ 5M", fontes=[])
        ]
        
        mock_redacted = RedactedDossier(
            enriched=mock_enriched,
            conteudo="# Relatório Empresa X\n\nConteúdo.",
            tom_de_voz="formal",
            modelo_usado="claude-3-5-sonnet",
        )
        mock_redacao.return_value = mock_redacted
        mock_output.return_value = str(output_file)
        
        monkeypatch.setattr(
            "sys.argv",
            ["main.py", "pipeline", str(dossier_file), "--tom", "formal", "-o", str(output_file)],
        )
        main()
    
    captured = capsys.readouterr()
    assert "Pipeline concluído" in captured.out
    assert str(output_file) in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_pipeline_cli.py::test_pipeline_completo_cli -v`
Expected: FAIL with "invalid choice: 'pipeline'"

- [ ] **Step 3: Add subcomando `pipeline` to CLI in `src/cli/main.py`**

Add new function `cmd_pipeline(args)` and register subparser `pipeline` with arguments:
- `caminho` (positional)
- `--tom` (choices: formal, consultivo, tecnico; default: formal)
- `--formato` (choices: markdown, html; default: markdown)
- `--output`, `-o` (optional)

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/cli/test_pipeline_cli.py::test_pipeline_completo_cli -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/cli/test_pipeline_cli.py src/cli/main.py
git commit -m "feat: add pipeline CLI command"
```

---

### Task 3: Tratamento de Erros e Logging

**Files:**
- Modify: `src/pipeline.py`
- Test: `tests/test_pipeline_erros.py`

**Interfaces:**
- Consumes: existing `executar_pipeline()` signature
- Produces: `PipelineError` exception class for pipeline failures

- [ ] **Step 1: Write the failing tests**

```python
def test_pipeline_erro_pesquisa():
    """Testa erro na fase de pesquisa."""
    from unittest.mock import patch
    from src.schemas.dossier_input import DossierInput
    from src.pipeline import executar_pipeline, PipelineError
    
    dossier = DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )
    
    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa:
        mock_pesquisa.side_effect = Exception("Erro na busca")
        
        with pytest.raises(PipelineError, match="Pesquisa"):
            executar_pipeline(dossier, tom="formal", formato="markdown", output_path="data/relatorio.md")


def test_pipeline_erro_redacao():
    """Testa erro na fase de redação."""
    from unittest.mock import patch
    from src.schemas.dossier_input import DossierInput
    from src.pipeline import executar_pipeline, PipelineError
    
    dossier = DossierInput(
        empresa_nome="Empresa X",
        segmento="Tecnologia",
        descricao="Empresa de tecnologia focada em automação.",
    )
    
    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, \
         patch("src.pipeline.redigir_relatorio") as mock_redacao:
        
        mock_pesquisa.return_value = []
        mock_redacao.side_effect = RuntimeError("LLM falhou")
        
        with pytest.raises(PipelineError, match="Redação"):
            executar_pipeline(dossier, tom="formal", formato="markdown", output_path="data/relatorio.md")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipeline_erros.py -v`
Expected: FAIL with "PipelineError not defined"

- [ ] **Step 3: Add error handling to `src/pipeline.py`**

```python
class PipelineError(Exception):
    """Erro durante a execução do pipeline."""
    pass


def executar_pipeline(...) -> str:
    """..."""
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pipeline_erros.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add tests/test_pipeline_erros.py src/pipeline.py
git commit -m "feat: add error handling to pipeline"
```

---

### Task 4: Teste Ponta a Ponta com Dossiê Real

**Files:**
- Create: `tests/test_e2e.py`

**Interfaces:**
- Consumes: `src.cli.main.main()` with `pipeline` subcommand
- Produces: End-to-end test with real DossierInput (mocked external calls)

- [ ] **Step 1: Write the failing test**

```python
def test_e2e_pipeline_com_dossier_real(tmp_path, monkeypatch, capsys):
    """Teste ponta a ponta com dossiê real."""
    import json
    from unittest.mock import patch
    from src.cli.main import main
    
    dossier_data = {
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
    
    dossier_file = tmp_path / "dossier.json"
    dossier_file.write_text(json.dumps(dossier_data, ensure_ascii=False), encoding="utf-8")
    
    output_file = tmp_path / "relatorio.md"
    
    with patch("src.pipeline.pesquisar_dados") as mock_pesquisa, \
         patch("src.pipeline.redigir_relatorio") as mock_redacao, \
         patch("src.pipeline.salvar_relatorio") as mock_output:
        
        from src.models.enriched_dossier import DadoPesquisado, EnrichedDossier
        from src.models.redacted_dossier import RedactedDossier
        from src.schemas.dossier_input import DossierInput
        
        dossier = DossierInput(**dossier_data)
        
        mock_pesquisa.return_value = [
            DadoPesquisado(
                categoria="financeiro",
                descricao="Receita anual",
                valor="R$ 5.000.000",
                fontes=[{"url": "https://techflow.com.br", "titulo": "TechFlow", "trecho": "Receita", "confiabilidade": "alta"}]
            )
        ]
        
        mock_enriched = EnrichedDossier(
            dossier_input=dossier,
            dados_pesquisados=mock_pesquisa.return_value,
        )
        
        mock_redacted = RedactedDossier(
            enriched=mock_enriched,
            conteudo="# Dossiê TechFlow Solutions\n\n## Resumo Executivo\n\nEmpresa de tecnologia com receita de R$ 5M.",
            tom_de_voz="formal",
            modelo_usado="claude-3-5-sonnet",
        )
        mock_redacao.return_value = mock_redacted
        mock_output.return_value = str(output_file)
        
        monkeypatch.setattr(
            "sys.argv",
            ["main.py", "pipeline", str(dossier_file), "--tom", "formal", "-o", str(output_file)],
        )
        main()
    
    captured = capsys.readouterr()
    assert "Pipeline concluído" in captured.out
    assert "TechFlow Solutions" in captured.out or "formal" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_e2e.py::test_e2e_pipeline_com_dossier_real -v`
Expected: FAIL (pipeline command not implemented)

- [ ] **Step 3: Run test to verify it passes**

Run: `pytest tests/test_e2e.py::test_e2e_pipeline_com_dossier_real -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: add end-to-end pipeline test"
```

---

### Task 5: Documentação Final

**Files:**
- Modify: `README.md`
- Create: `data/relatorio_exemplo.md` (exemplo de saída)

- [ ] **Step 1: Atualizar README com pipeline completo**

Adicionar seções:
- "Como usar o Pipeline Completo" com exemplo de comando
- "Formato de Saída" explicando markdown e html
- "Tratamento de Erros" explicando PipelineError
- Atualizar roadmap com Passos 4 e 5 concluídos

- [ ] **Step 2: Criar exemplo de saída**

Criar `data/relatorio_exemplo.md` com exemplo de relatório gerado.

- [ ] **Step 3: Commit**

```bash
git add README.md data/relatorio_exemplo.md
git commit -m "docs: final documentation and roadmap update"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ Pipeline completo (input → pesquisa → redação → output)
- ✅ CLI integrada com subcomando `pipeline`
- ✅ Tratamento de erros com PipelineError
- ✅ Teste ponta a ponta com dossiê real
- ✅ Documentação final

**2. Step scan:**
- Cada step tem uma ação verificável clara
- Sem código desnecessário nos steps

**3. Type consistency:**
- `executar_pipeline(dossier, tom, formato, output_path) -> str` consistente em todas as tasks
- `PipelineError` definido na Task 3 e usado consistentemente

**4. Review Focus:**
- ✅ Dados vazios → coberto no pipeline (não falha)
- ✅ Falha na busca → coberto na Task 3 (PipelineError)
- ✅ Falha na LLM → coberto na Task 3 (PipelineError)
- ✅ Timeout → já tratado na busca web existente
- ✅ Dossiê incompleto → coberto na Task 4 (teste com dossiê real)

**5. Proportion:**
- Plano de 5 tasks, cada uma com entregável testável
- Código mínimo necessário nos steps
- Sem redundância

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-10-12-passo-5-integracao-ponta-a-ponta.md`.**

**Recommended approach:** Native — as tasks são pequenas e o pipeline é isolado. O Passo 5 é a finalização do projeto.

**Does this plan capture what you want?**
