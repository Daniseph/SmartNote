#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_similaridade.py
Descrição: Testes unitários para a função de similaridade do cosseno.
===============================================================================
"""

import numpy as np
from modulos.similaridade import SimilaridadeUtils

# ==============================================================================
# Testes de Similaridade
# ==============================================================================

def test_similaridade_identica():
    """
    Testa se vetores idênticos retornam similaridade máxima (1.0).
    """
    v1 = np.array([1, 2, 3])
    v2 = np.array([1, 2, 3])
    score = SimilaridadeUtils.similaridade(v1, v2)
    assert score == 1.0

def test_similaridade_ortogonal():
    """
    Testa se vetores ortogonais retornam similaridade nula (0.0).
    """
    v1 = np.array([1, 0])
    v2 = np.array([0, 1])
    score = SimilaridadeUtils.similaridade(v1, v2)
    assert score == 0.0

def test_similaridade_parcial():
    """
    Testa se vetores parcialmente semelhantes retornam valor intermediário.
    """
    v1 = np.array([1, 0])
    v2 = np.array([1, 1])
    score = SimilaridadeUtils.similaridade(v1, v2)
    assert 0.7 < score < 0.8  # Aproximadamente 0.7071

def test_similaridade_com_vetores_2d():
    """
    Testa se a função aceita vetores bidimensionais como entrada.
    """
    v1 = np.array([[1, 0]])
    v2 = np.array([[0, 1]])
    score = SimilaridadeUtils.similaridade(v1, v2)
    assert score == 0.0

def test_entrada_unidimensional_e_bidimensional():
    """
    Testa combinação entre vetor 1D e 2D como entrada.
    """
    v1 = np.array([1, 0])
    v2 = np.array([[1, 0]])
    score = SimilaridadeUtils.similaridade(v1, v2)
    assert score == 1.0

def test_similaridade_vetores_normalizados():
    """
    Testa similaridade entre vetores com mesma direção, mas magnitude diferente.
    """
    v1 = np.array([3, 4])
    v2 = np.array([6, 8])
    v1_norm = v1 / np.linalg.norm(v1)
    v2_norm = v2 / np.linalg.norm(v2)

    score = SimilaridadeUtils.similaridade(v1_norm, v2_norm)
    assert score == 1.0

def test_similaridade_vetores_aleatorios():
    """
    Testa se o resultado da similaridade entre vetores aleatórios está entre -1 e 1.
    """
    np.random.seed(42)
    v1 = np.random.rand(128)
    v2 = np.random.rand(128)
    score = SimilaridadeUtils.similaridade(v1, v2)

    assert -1.0 <= score <= 1.0
    assert isinstance(score, float)
