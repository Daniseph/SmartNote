#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_conceitos.py
Descrição: Testes unitários para extração de conceitos básicos e validação
           de termos no módulo de conceitos.
===============================================================================
"""

import pytest
from modulos.conceitos import extrator_conceitos

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def extrator():
    """
    Fixture que retorna o módulo de extração de conceitos.

    Returns:
        módulo: Referência ao módulo extrator_conceitos.
    """
    return extrator_conceitos

# ==============================================================================
# Testes de Extração de Conceitos
# ==============================================================================

def test_extrair_conceitos_basicos_simples(extrator):
    """
    Verifica se conceitos esperados são extraídos corretamente de um texto simples.
    """
    texto = "Este é um teste com inteligência artificial e redes neurais."
    conceitos = extrator.extrair_conceitos_basicos(texto)

    termos = [c.termo.lower() for c in conceitos]

    assert any("inteligência" in t or "artificial" in t for t in termos)
    assert any("redes" in t or "neurais" in t for t in termos)


def test_extrair_conceitos_basicos_stopwords(extrator):
    """
    Garante que palavras vazias (stopwords) não sejam reconhecidas como conceitos.
    """
    texto = "o e a de que em com por para como mais"
    conceitos = extrator.extrair_conceitos_basicos(texto)

    assert conceitos == []

# ==============================================================================
# Testes de Validação de Conceitos
# ==============================================================================

def test_validar_conceito():
    """
    Testa a função interna de validação de termos como conceitos relevantes.
    """
    assert extrator_conceitos._validar_conceito("Machine Learning") is True
    assert extrator_conceitos._validar_conceito("o") is False
    assert extrator_conceitos._validar_conceito("123") is False
    assert extrator_conceitos._validar_conceito("@#$") is False
