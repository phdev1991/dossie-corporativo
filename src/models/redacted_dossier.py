"""Modelo do dossiê redigido (relatório final)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.models.enriched_dossier import EnrichedDossier


class RedactedDossier(BaseModel):
    """Dossiê após o processo de redação comercial."""

    enriched: EnrichedDossier
    conteudo: str
    tom_de_voz: Literal["formal", "consultivo", "tecnico"]
    data_redacao: datetime = Field(default_factory=datetime.now)
    modelo_usado: str

    def to_dict(self) -> dict:
        """Retorna o modelo como dicionário serializável em JSON."""
        return self.model_dump(mode="json")
