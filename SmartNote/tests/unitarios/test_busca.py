#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_busca.py
Descrição: Testes unitários para o módulo de busca textual nas notas.
===============================================================================
"""

import pytest
from modulos.busca import buscar

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def notas_mock():
    """
    Cria uma lista de notas simuladas para testes.

    Returns:
        list[dict]: Notas com conteúdo variado.
    """
    return [
        {"titulo": "Nota1", "conteudo": "Hoje estudei machine learning e foi produtivo."},
        {"titulo": "Nota2", "conteudo": "A reunião sobre aprendizado de máquina foi interessante."},
        {"titulo": "Nota3", "conteudo": "Fiz uma pausa, sem conteúdo técnico hoje."}
    ]


# ==============================================================================
# Testes de Busca
# ==============================================================================

def test_busca_simples(notas_mock):
    """
    Testa busca simples com palavra-chave direta.
    """
    resultados = buscar("machine", notas_mock)

    assert len(resultados) == 1
    assert "machine" in resultados[0].trecho.lower()


def test_busca_ignorar_acentos(notas_mock):
    """
    Verifica se a busca funciona ignorando acentuação.
    """
    config = {"ignorar_acentos": True}
    resultados = buscar("aprendizado", notas_mock, config)

    assert any("aprendizado" in r.trecho.lower() for r in resultados)


def test_busca_diferenciar_maiusculas(notas_mock):
    """
    Testa diferenciação de maiúsculas e minúsculas na busca.
    """
    config = {"diferenciar_maiusculas": True}

    resultados = buscar("Hoje", notas_mock, config)
    assert any("Hoje" in r.trecho for r in resultados)

    resultados_minusculo = buscar("hoje", notas_mock, config)
    assert all("Hoje" not in r.trecho for r in resultados_minusculo)


def test_busca_regex(notas_mock):
    """
    Verifica se expressões regulares funcionam na busca.
    """
    config = {
        "modo_regex": True,
        "ignorar_acentos": True
    }

    resultados = buscar(r"aprendiz.*máquina", notas_mock, config)

    assert len(resultados) == 1
    assert "aprendizado de máquina" in resultados[0].trecho.lower()


def test_busca_sem_resultados(notas_mock):
    """
    Confirma que nenhum resultado é retornado se não houver correspondência.
    """
    resultados = buscar("quantum computing", notas_mock)

    assert resultados == []

