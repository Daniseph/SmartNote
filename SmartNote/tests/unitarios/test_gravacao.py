#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_gravacao.py
Descrição: Testes unitários para as funções de gravação de notas (individuais e em lote).
===============================================================================
"""

import pytest
from pathlib import Path
from modulos.gravacao import gravador_notas

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def nota_teste(tmp_path):
    """
    Cria uma nota temporária de teste.

    Args:
        tmp_path (Path): Diretório temporário gerado pelo pytest.

    Returns:
        dict: Dicionário representando uma nota.
    """
    caminho = tmp_path / "nota_teste.md"
    return {
        "conteudo": "Conteúdo da nota de teste.\n---\nautor: Teste",
        "caminho": str(caminho)
    }

# ==============================================================================
# Testes de Gravação
# ==============================================================================

def test_gravar_nota_simples(nota_teste):
    """
    Testa se uma nota individual é corretamente gravada em ficheiro.

    Args:
        nota_teste (dict): Nota gerada pelo fixture.
    """
    sucesso, erro = gravador_notas.gravar_nota_individual(nota_teste)

    assert sucesso is True
    assert erro is None

    caminho_esperado = Path(nota_teste["caminho"])
    assert caminho_esperado.exists()

    conteudo = caminho_esperado.read_text(encoding='utf-8')
    assert "Conteúdo da nota" in conteudo
    assert "autor" in conteudo

def test_gravar_varias_notas(tmp_path):
    """
    Testa a gravação de várias notas em lote.

    Args:
        tmp_path (Path): Diretório temporário para armazenar notas.
    """
    notas = []
    for i in range(3):
        caminho = tmp_path / f"nota_teste_{i}.md"
        notas.append({
            "conteudo": f"Nota número {i}",
            "caminho": str(caminho)
        })

    resultado = gravador_notas.gravar_notas_lote(notas)

    assert resultado["sucesso"] == 3
    assert resultado["erros"] == []
