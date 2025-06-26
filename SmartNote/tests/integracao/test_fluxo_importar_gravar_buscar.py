#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_fluxo_importar_gravar_buscar.py
Descrição: Teste integrado de importação, busca e gravação de notas.
===============================================================================
"""

import os
import tempfile

from modulos.importacao import importar_diretorio
from modulos.busca import buscar
from modulos.gravacao import gravador_notas

# ==============================================================================
# Testes de Fluxo Integrado
# ==============================================================================

def test_importar_buscar_gravar():
    """
    Testa o fluxo completo de:
    - criação de nota temporária
    - importação com validação
    - busca de termos na nota
    - gravação num novo diretório

    Returns:
        None. Verifica integridade com assertivas internas.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Criar ficheiro de nota temporária
        caminho_nota = os.path.join(tmpdir, "nota_teste.md")
        conteudo = (
            "---\n"
            "titulo: Teste\n"
            "---\n"
            "Este é um teste de integração com inteligência artificial."
        )

        with open(caminho_nota, "w", encoding="utf-8") as f:
            f.write(conteudo)

        # 2. Importar nota
        notas, erros = importar_diretorio(tmpdir)
        assert len(notas) == 1
        assert notas[0].valida
        assert not erros

        # 3. Buscar termo na nota importada
        notas_dict = [{
            "titulo": nota.titulo,
            "conteudo": nota.conteudo,
            "caminho": nota.caminho
        } for nota in notas]

        resultados = buscar("inteligência", notas_dict, {
            "ignorar_acentos": True,
            "diferenciar_maiusculas": False,
            "modo_regex": False,
            "usar_cache": False
        })

        assert any("inteligência" in r.trecho.lower() for r in resultados)

        # 4. Gravar nota num novo diretório
        destino = os.path.join(tmpdir, "gravadas")
        os.makedirs(destino, exist_ok=True)

        for nota in notas_dict:
            nome_ficheiro = os.path.basename(nota["caminho"])
            nota["caminho"] = os.path.join(destino, nome_ficheiro)

        resultado_gravacao = gravador_notas.gravar_notas_lote(notas_dict)

        assert resultado_gravacao["sucesso"] == 1
        assert not resultado_gravacao["erros"]
