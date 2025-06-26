#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: conftest.py
Descrição: Fixtures reutilizáveis para testes
===============================================================================
"""

import sys
import os
import pytest
from datetime import datetime

# ==============================================================================
# Ajuste de Caminho para Importações Relativas
# ==============================================================================

# Adiciona a raiz do projeto ao sys.path para facilitar os imports nos testes
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ==============================================================================
# Fixtures de Testes
# ==============================================================================

@pytest.fixture
def nota_teste():
    """
    Cria uma nota fictícia para testes isolados.

    Returns:
        dict: Estrutura simulada de uma nota.
    """
    return {
        "titulo": "nota_teste",
        "conteudo": "Conteúdo da nota de teste.",
        "caminho_absoluto": None,
        "data_modificacao": datetime.now(),
        "frontmatter": {"autor": "Teste"}
    }


@pytest.fixture
def notas_mock():
    """
    Gera uma lista de notas simuladas com variação de conteúdo técnico.

    Returns:
        list[dict]: Lista de notas para testes de busca ou análise.
    """
    return [
        {
            "titulo": "Nota1",
            "conteudo": "Hoje estudei machine learning e foi produtivo."
        },
        {
            "titulo": "Nota2",
            "conteudo": "A reunião sobre aprendizado de máquina foi interessante."
        },
        {
            "titulo": "Nota3",
            "conteudo": "Fiz uma pausa, sem conteúdo técnico hoje."
        }
    ]
