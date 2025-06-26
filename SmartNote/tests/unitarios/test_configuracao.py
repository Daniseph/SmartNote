#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: test_configurador.py
Descrição: Testes unitários para o módulo de configuração do sistema.
===============================================================================
"""

import json
import pytest
from modulos.configuracao import configurador

# ==============================================================================
# Fixture para Reset Automático
# ==============================================================================

@pytest.fixture(autouse=True)
def reset_config():
    """
    Garante que a configuração seja resetada antes de cada teste.
    """
    configurador.resetar_para_padrao()

# ==============================================================================
# Testes de Obtenção e Definição
# ==============================================================================

def test_obter_valor_existente():
    """
    Verifica se um valor padrão pode ser obtido corretamente.
    """
    valor = configurador.obter("modelo_ia", "nome")
    assert isinstance(valor, str)

def test_definir_e_obter_valor_temporario():
    """
    Define um valor temporário e verifica se é retornado corretamente.
    """
    configurador.definir("interface", "tema", "escuro")
    valor = configurador.obter("interface", "tema")
    assert valor == "escuro"

# ==============================================================================
# Testes de Exportação e Importação
# ==============================================================================

def test_exportar_e_importar_configuracoes(tmp_path):
    """
    Testa a exportação para ficheiro e posterior reimportação de configurações.
    
    Args:
        tmp_path (Path): Diretório temporário fornecido pelo pytest.
    """
    caminho = tmp_path / "config_exportada.json"

    configurador.exportar_configuracoes(str(caminho))
    assert caminho.exists()

    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        assert "modelo_ia" in dados

    # Modifica temporariamente e verifica que importação restaura valor original
    configurador.definir("links", "max_links_por_paragrafo", 999)
    configurador.importar_configuracoes(str(caminho))

    assert configurador.obter("links", "max_links_por_paragrafo") != 999

# ==============================================================================
# Teste de Reset para Padrões
# ==============================================================================

def test_resetar_configuracoes():
    """
    Garante que a configuração é restaurada aos valores padrão após reset.
    """
    configurador.definir("privacidade", "modo_offline", False)
    assert configurador.obter("privacidade", "modo_offline") is False

    configurador.resetar_para_padrao()
    assert configurador.obter("privacidade", "modo_offline") is True
