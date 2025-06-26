#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_importacao.py
Descrição: Testes de importação de notas a partir de ficheiros Markdown.
===============================================================================
"""

import pytest
from modulos.importacao import importar_diretorio

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def diretorio_temporario(tmp_path):
    """
    Cria um diretório temporário para testes.

    Args:
        tmp_path (Path): Diretório temporário criado automaticamente pelo pytest.

    Yields:
        Path: Caminho para o diretório.
    """
    yield tmp_path

# ==============================================================================
# Testes de Importação
# ==============================================================================

def test_importar_arquivo_com_frontmatter(diretorio_temporario):
    """
    Testa a importação de um ficheiro com metadados (frontmatter YAML).

    Args:
        diretorio_temporario (Path): Diretório onde o ficheiro será criado.
    """
    arquivo = diretorio_temporario / "nota.md"
    conteudo = "---\ntitulo: Teste\nautor: Autor\n---\nConteúdo da nota."
    arquivo.write_text(conteudo, encoding="utf-8")

    notas, erros = importar_diretorio(str(diretorio_temporario))

    assert len(notas) == 1
    nota = notas[0]
    assert nota.titulo == "nota"
    assert nota.frontmatter.get("titulo") == "Teste"
    assert nota.frontmatter.get("autor") == "Autor"
    assert "Conteúdo da nota" in nota.conteudo
    assert nota.valida is True
    assert nota.erro is None
    assert erros == []

def test_importar_arquivo_sem_frontmatter(diretorio_temporario):
    """
    Testa a importação de um ficheiro sem frontmatter.

    Args:
        diretorio_temporario (Path): Diretório onde o ficheiro será criado.
    """
    arquivo = diretorio_temporario / "nota.txt"
    conteudo = "Esta é uma nota sem metadados."
    arquivo.write_text(conteudo, encoding="utf-8")

    notas, erros = importar_diretorio(str(diretorio_temporario))

    assert len(notas) == 1
    nota = notas[0]
    assert nota.titulo == "nota"
    assert nota.frontmatter == {}
    assert "sem metadados" in nota.conteudo
    assert nota.valida is True
    assert nota.erro is None
    assert erros == []

def test_importar_diretorio_vazio(diretorio_temporario):
    """
    Testa a importação de um diretório vazio.

    Args:
        diretorio_temporario (Path): Diretório sem ficheiros.
    """
    notas, erros = importar_diretorio(str(diretorio_temporario))
    assert notas == []
    assert erros == []

def test_importar_arquivo_com_codificacao_invalida(diretorio_temporario):
    """
    Testa a importação de um ficheiro com codificação inválida.

    Args:
        diretorio_temporario (Path): Diretório onde o ficheiro será criado.
    """
    arquivo = diretorio_temporario / "corrompido.txt"
    arquivo.write_bytes(b"\xff\xfe\x00\x00")  # conteúdo binário ilegível

    notas, erros = importar_diretorio(str(diretorio_temporario))

    assert len(notas) == 1
    nota = notas[0]
    assert nota.valida is False
    assert nota.erro is not None
    assert "Conteúdo ilegível" in nota.erro
    assert any("corrompido" in erro for erro in erros)
