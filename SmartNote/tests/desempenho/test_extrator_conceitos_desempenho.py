#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_extrator_conceitos_desempenho.py
Descrição: Testes de desempenho dos extratores de conceitos (básico e avançado).
===============================================================================
"""

import time
import pytest

from modulos.conceitos import ExtratorConceitos

# ==============================================================================
# Configurações e Condições
# ==============================================================================

# Limites máximos de tempo para os testes de desempenho (em segundos)
LIMITE_BASICO = 1.5
LIMITE_AVANCADO = 50.0

# Verifica se spaCy está instalado
try:
    import spacy
    SPACY_DISPONIVEL = True
except ImportError:
    SPACY_DISPONIVEL = False

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def texto_longo():
    """
    Gera um texto longo simulando muitos parágrafos.

    Returns:
        str: Texto repetido para teste de desempenho.
    """
    paragrafo = (
        "A inteligência artificial está revolucionando o mundo com aprendizado profundo, "
        "redes neurais, algoritmos genéticos e mineração de dados. "
    )
    return paragrafo * 1000  # Aproximadamente 1000 parágrafos

# ==============================================================================
# Testes de Desempenho
# ==============================================================================

@pytest.mark.performance
def test_extrator_basico_desempenho(texto_longo):
    """
    Verifica se o extrator básico consegue processar texto extenso dentro do tempo limite.

    Args:
        texto_longo (str): Texto gerado pela fixture.

    Returns:
        None
    """
    extrator = ExtratorConceitos()

    inicio = time.time()
    conceitos = extrator.extrair_conceitos_basicos(texto_longo)
    duracao = time.time() - inicio

    assert isinstance(conceitos, list)
    assert len(conceitos) > 0
    assert duracao < LIMITE_BASICO, (
        f"Extração básica demorou {duracao:.2f}s (limite: {LIMITE_BASICO}s)"
    )

@pytest.mark.performance
@pytest.mark.skipif(not SPACY_DISPONIVEL, reason="spaCy não está disponível")
def test_extrator_avancado_desempenho(texto_longo):
    """
    Verifica se o extrator avançado com spaCy realiza a extração dentro do tempo limite.

    Args:
        texto_longo (str): Texto gerado pela fixture.

    Returns:
        None
    """
    extrator = ExtratorConceitos()

    inicio = time.time()
    conceitos = extrator.extrair_conceitos_avancados(texto_longo, titulo_nota="Nota Teste")
    duracao = time.time() - inicio

    assert isinstance(conceitos, list)
    assert len(conceitos) > 0
    assert duracao < LIMITE_AVANCADO, (
        f"Extração avançada demorou {duracao:.2f}s (limite: {LIMITE_AVANCADO}s)"
    )
