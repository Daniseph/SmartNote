#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_geracao_links_literais_semanticos.py
Descrição: Teste da aplicação de links semânticos e literais sobre parágrafos.
===============================================================================
"""

import re
import pytest

from modulos.links_semanticos import GeradorLinksSemanticos
from modulos.similaridade import SimilaridadeUtils
from modulos.conceitos import extrator_conceitos

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def notas_simuladas():
    """
    Conjunto de notas simuladas para teste.

    Returns:
        list[dict]: Lista de dicionários representando notas.
    """
    return [
        {
            "titulo": "Aprendizagem Supervisionada",
            "conteudo": "A aprendizagem supervisionada é usada quando há dados rotulados para treinar modelos de classificação."
        },
        {
            "titulo": "Treinamento Supervisionado",
            "conteudo": "Neste modelo, a máquina é treinada com dados anotados."
        },
        {
            "titulo": "Redes Neuronais",
            "conteudo": "As redes neuronais são uma técnica poderosa para tarefas de previsão."
        }
    ]

# ==============================================================================
# Testes
# ==============================================================================

def test_aplicacao_de_links_literais_ou_semanticos(notas_simuladas):
    """
    Verifica se termos relacionados com títulos de notas são corretamente linkados,
    usando embeddings e limiar de similaridade reduzido.

    Args:
        notas_simuladas (fixture): Notas artificiais para simulação de indexação.

    Returns:
        None. Validações feitas com assertivas.
    """
    paragrafo = (
        "Durante o treino, a rede aprende a reconhecer padrões em exemplos "
        "previamente etiquetados."
    )

    gerador = GeradorLinksSemanticos()
    gerador.configurar_parametros(limiar_similaridade=0.05)
    gerador.criar_indice_titulos(notas_simuladas)

    titulos_similares = gerador._buscar_titulos_similares(paragrafo)
    assert titulos_similares, "Nenhum título similar encontrado"

    termos_paragrafo = extrator_conceitos.extrair_conceitos_avancados(paragrafo)
    termos_para_linkar = set()

    for titulo_similar, _ in titulos_similares:
        nota_destino = next(
            (n for n in notas_simuladas if n["titulo"] == titulo_similar), None
        )
        if nota_destino:
            termos_similar = extrator_conceitos.extrair_conceitos_avancados(
                nota_destino["conteudo"]
            )

            if not termos_paragrafo or not termos_similar:
                continue

            termos_similar_texto = [c.termo for c in termos_similar]
            termos_paragrafo_texto = [c.termo for c in termos_paragrafo]

            emb_origem = gerador.modelo_embeddings.encode(termos_similar_texto)
            emb_destino = gerador.modelo_embeddings.encode(termos_paragrafo_texto)

            for i, vetor_o in enumerate(emb_origem):
                termo_o = termos_similar_texto[i]
                for j, vetor_d in enumerate(emb_destino):
                    termo_d = termos_paragrafo_texto[j]
                    score = SimilaridadeUtils.similaridade(vetor_o, vetor_d)
                    if score >= gerador.limiar_similaridade:
                        termos_para_linkar.add(termo_d)

    texto_com_links = paragrafo
    for termo in sorted(termos_para_linkar, key=len, reverse=True):
        padrao = re.compile(rf'\b({re.escape(termo)})\b', flags=re.IGNORECASE)
        texto_com_links = padrao.sub(r'[[\1]]', texto_com_links)

    assert "[[" in texto_com_links, "Nenhum termo foi linkado"
    assert any(t in texto_com_links for t in termos_para_linkar), "Termos esperados não foram marcados"
