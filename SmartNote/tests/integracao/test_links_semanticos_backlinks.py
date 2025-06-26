#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_links_semanticos_backlinks.py
Descrição: Testa a geração de links semânticos e registro de backlinks entre notas.
===============================================================================
"""

from modulos.links_semanticos import GeradorLinksSemanticos
from modulos.backlinks import GestorBacklinks

# ==============================================================================
# Testes
# ==============================================================================

def test_geracao_links_semanticos_e_backlinks():
    """
    Testa se links semânticos entre notas são corretamente gerados e
    se os backlinks são registrados corretamente.

    Returns:
        None. Usa assertivas para validação automática.
    """

    # 1. Criar duas notas com conteúdo relacionado
    notas = [
        {
            "titulo": "Nota IA",
            "conteudo": "Aprendi sobre inteligência artificial e redes neurais."
        },
        {
            "titulo": "Nota Cérebro",
            "conteudo": "As redes neurais são inspiradas no cérebro humano."
        }
    ]

    # 2. Instanciar gerador e gestor
    gerador = GeradorLinksSemanticos()
    gestor = GestorBacklinks()

    # 3. Gerar índice e links sugeridos
    gerador.criar_indice_titulos(notas)
    links_gerados = gerador.gerar_links_sugeridos(notas)

    # 4. Registrar backlinks com base nos links semânticos
    for titulo_origem, links in links_gerados.items():
        for link in links:
            gestor.registrar_link_semantico(
                origem=titulo_origem,
                destino=link.nota_destino,
                termo=link.termo
            )

    # 5. Verificar backlinks da nota de destino
    backlinks_para_b = gestor.obter_backlinks_para("Nota Cérebro")

    assert any(b["nota_origem"] == "Nota IA" for b in backlinks_para_b), \
        "Backlink de 'Nota IA' não encontrado"

    assert any("redes" in b["termo"].lower() for b in backlinks_para_b), \
        "Termo 'redes' não encontrado no backlink"
