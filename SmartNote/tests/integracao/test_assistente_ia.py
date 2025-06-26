#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_assistente_ia.py
Descrição: Testes unitários para o módulo de Assistente IA Avançado.
===============================================================================
"""

from modulos.assistente_ia import AssistenteIAAvancado

# ==============================================================================
# Testes - Assistente IA
# ==============================================================================

def test_assistente_ia_resposta_basica_sem_faiss():
    """
    Testa o comportamento básico do assistente IA mesmo sem FAISS ou servidor local ativo.

    Verifica se:
    - O método retorna um dicionário.
    - A resposta contém as chaves esperadas.
    - O campo de contexto indica se foi usado ou não.

    Returns:
        None. Usa asserts internos do pytest.
    """

    assistente = AssistenteIAAvancado()

    # Criar índice com notas simuladas (mesmo sem FAISS, deve seguir fluxo alternativo)
    notas = [
        {
            "titulo": "Nota AI",
            "conteudo": "Estudo sobre inteligência artificial e aprendizado profundo."
        },
        {
            "titulo": "Nota ML",
            "conteudo": "Machine learning supervisionado e redes neurais convolucionais."
        }
    ]
    assistente.criar_indice_conteudo(notas)

    # Realizar pergunta
    pergunta = "O que é aprendizado profundo?"
    resposta = assistente.gerar_resposta_com_rag(pergunta)

    # Asserções principais
    assert isinstance(resposta, dict)
    assert "resposta" in resposta
    assert "documentos_usados" in resposta
    assert "metodo" in resposta
    assert isinstance(resposta.get("contexto_usado", None), bool)
