#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: main.py
Descrição: Ponto de entrada principal do SmartNote.
===============================================================================
"""

import sys
import os
import argparse
import logging
import traceback
import subprocess


# ==============================================================================
# Configuração de logging
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Inserir caminho para módulos locais
# ==============================================================================

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modulos'))


# ==============================================================================
# Funções Utilitárias
# ==============================================================================

def importar_seguro(modulo, objeto=None):
    """
    Importa dinamicamente um módulo ou objeto de forma segura.

    @param modulo: Nome do módulo a importar.
    @param objeto: (Opcional) Nome do objeto dentro do módulo.
    @return: Objeto importado ou None se falhar.
    """
    try:
        mod = __import__(modulo, fromlist=[objeto] if objeto else [])
        return getattr(mod, objeto) if objeto else mod
    except ImportError as e:
        logger.error(f"Erro ao importar '{modulo}': {e}")
        logger.debug(traceback.format_exc())
        return None


# ==============================================================================
# Execução de Testes Automatizados
# ==============================================================================

def executar_testes(tipo='unitarios'):
    """
    Executa testes automáticos com pytest, por tipo (unitários, integração, desempenho).

    @param tipo: String indicando o tipo de testes a executar.
    """
    pasta_teste = os.path.join(os.path.dirname(__file__), 'tests', tipo.lower())

    if not os.path.isdir(pasta_teste):
        logger.error(f"Pasta de testes não encontrada para o tipo: {tipo}")
        sys.exit(1)

    logger.info(f"Executando testes '{tipo}' em: {pasta_teste}")
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", pasta_teste, "-v", "--disable-warnings"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(resultado.stdout)
        logger.info("Testes concluídos com sucesso.")
    except subprocess.CalledProcessError as e:
        logger.error("Alguns testes falharam:")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)


# ==============================================================================
# Inicialização da Interface Gráfica
# ==============================================================================

def iniciar_interface():
    """
    Inicializa a interface gráfica da aplicação usando PyQt5.
    """
    from PyQt5.QtWidgets import QApplication
    App = importar_seguro('interface.interface', 'SmartNoteApp')
    if not App:
        logger.error("Falha ao carregar a interface gráfica.")
        sys.exit(1)

    app = QApplication.instance() or QApplication(sys.argv)
    janela = App()
    janela.show()
    sys.exit(app.exec_())


# ==============================================================================
# Função Principal
# ==============================================================================

def main():
    """
    Função principal: interpreta argumentos de linha de comando e inicia testes ou GUI.
    """
    parser = argparse.ArgumentParser(description='SmartNote - Sistema de Notas Inteligente')
    parser.add_argument('--testes', choices=['unitarios', 'integracao', 'desempenho'], help='Executar testes por tipo')
    args = parser.parse_args()

    if args.testes:
        logger.info(f"Executando testes do tipo: {args.testes}")
        executar_testes(args.testes)
    else:
        logger.info("Inicializando a interface gráfica principal.")
        iniciar_interface()


# ==============================================================================
# Execução Direta
# ==============================================================================

if __name__ == '__main__':
    main()
