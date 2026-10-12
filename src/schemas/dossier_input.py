"""Modelo Pydantic para o formato de entrada do dossiê corporativo."""

import re

from pydantic import BaseModel, Field, field_validator


class DossierInput(BaseModel):
    """Formato de entrada do dossiê corporativo existente."""

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
        """Valida o formato do CNPJ: 00.000.000/0000-00."""
        if v is None:
            return v
        if not re.match(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", v):
            raise ValueError("CNPJ deve estar no formato 00.000.000/0000-00")
        return v

    def to_dict(self) -> dict:
        """Retorna o modelo como dicionário."""
        return self.model_dump()
