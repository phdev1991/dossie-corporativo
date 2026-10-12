"""Modelo do dossiê enriquecido com dados de pesquisa externa."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.dossier_input import DossierInput


class FonteEncontrada(BaseModel):
    """Fonte de informação encontrada durante a pesquisa externa."""

    url: str
    titulo: str
    trecho: str
    confiabilidade: Literal["alta", "media", "baixa"]


class DadoPesquisado(BaseModel):
    """Dado coletado pelos subagentes, com suas fontes."""

    categoria: str
    descricao: str
    valor: str | float | None = None
    fontes: list[FonteEncontrada] = Field(default_factory=list)
    conflito: bool = False


class EnrichedDossier(BaseModel):
    """Dossiê enriquecido: entrada validada + dados coletados."""

    dossier_input: DossierInput
    dados_pesquisados: list[DadoPesquisado] = Field(default_factory=list)
    data_enriquecimento: datetime = Field(default_factory=datetime.now)

    @property
    def total_fontes(self) -> int:
        """Número total de fontes coletadas em todos os dados pesquisados."""
        return sum(len(d.fontes) for d in self.dados_pesquisados)

    def to_dict(self) -> dict:
        """Retorna o modelo como dicionário serializável em JSON."""
        data = self.model_dump(mode="json")
        data["total_fontes"] = self.total_fontes
        return data
