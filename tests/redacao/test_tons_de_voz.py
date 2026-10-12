"""Testes para as diretrizes de tom de voz."""

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
