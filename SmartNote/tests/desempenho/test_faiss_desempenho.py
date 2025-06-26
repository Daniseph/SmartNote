#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_faiss_desempenho.py
Descrição: Testes de desempenho da geração de links semânticos com FAISS.
===============================================================================
"""

import time
import pytest
import warnings
from typing import List

from modulos.gerador_links import GeradorLinksAvancado, LinkSugerido

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def notas_simuladas():
    """
    Gera uma lista de notas simuladas com conteúdo repetitivo e variação numérica.

    Returns:
        list[dict]: Lista de dicionários representando notas.
    """
    base = (
        "A inteligência artificial está revolucionando o mundo. "
        "Redes neurais e aprendizado profundo são técnicas essenciais em IA moderna. "
    )
    return [{"titulo": f"Nota {i}", "conteudo": base + f" Exemplo número {i}."} for i in range(100)]

# ==============================================================================
# Testes de Desempenho
# ==============================================================================

@pytest.mark.performance
def test_geracao_links_semanticos_com_faiss(notas_simuladas):
    """
    Testa a criação de índice semântico FAISS e geração de links com desempenho aceitável.

    Args:
        notas_simuladas (list): Lista de notas fornecida pela fixture.

    Returns:
        None
    """
    gerador = GeradorLinksAvancado()
    gerador.modo_semantico = True  # Essencial para ativar uso de embeddings

    # Construção do índice FAISS
    t0 = time.time()
    gerador.criar_indice_faiss(notas_simuladas)
    tempo_indice = time.time() - t0

    if tempo_indice > 3.0:
        warnings.warn(f"Construção do índice FAISS demorou {tempo_indice:.2f}s (limite: 3.0s)")

    # Geração de links semânticos
    tempos_links = []
    total_links = 0

    for nota in notas_simuladas:
        t_ini = time.time()
        links: List[LinkSugerido] = gerador.processar_nota_para_links(nota, notas_simuladas)
        duracao = time.time() - t_ini

        tempos_links.append(duracao)
        total_links += len(links)

        # Verificação mínima: ao menos 1 link para outra nota
        assert any(link.nota_destino != nota["titulo"] for link in links), \
            f"Nenhum link válido gerado para {nota['titulo']}"

    tempo_medio = sum(tempos_links) / len(tempos_links)

    if tempo_medio > 0.1:
        warnings.warn(
            f"Tempo médio para gerar links por nota é alto: {tempo_medio:.4f}s (limite: 0.1s)"
        )
