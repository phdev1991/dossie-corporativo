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
            cnpj="12345678000190",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
        )


def test_dossier_input_campos_extras_rejeitados():
    with pytest.raises(ValidationError):
        DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Empresa de tecnologia focada em automação.",
            campo_desconhecido="valor",
        )


def test_dossier_input_descricao_muito_curta():
    with pytest.raises(ValidationError):
        DossierInput(
            empresa_nome="Empresa X",
            segmento="Tecnologia",
            descricao="Curta",
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
