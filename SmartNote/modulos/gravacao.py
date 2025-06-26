#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: gravacao.py
Descrição: Módulo de gravação de notas no sistema de ficheiros.
===============================================================================
"""

import os
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class GravadorNotas:
    """
    Classe responsável por gravar notas no sistema de ficheiros local.
    """

    def __init__(self, diretorio_notas: str = "."):
        """
        Inicializa o gravador com um diretório base.

        Args:
            diretorio_notas (str): Diretório onde as notas serão guardadas, por padrão ".".
        """
        self.diretorio_notas = diretorio_notas

    def gravar_nota_individual(self, nota: Dict) -> Tuple[bool, Optional[str]]:
        """
        Grava uma nota individual no caminho indicado, criando diretórios se necessário.

        Args:
            nota (Dict): Dicionário contendo pelo menos 'conteudo' e 'caminho'.

        Returns:
            Tuple[bool, Optional[str]]: Sucesso da operação e mensagem de erro (se houver).
        """
        caminho = nota.get('caminho', '')
        conteudo = nota.get('conteudo', '')

        if not caminho:
            return False, "Caminho do ficheiro não especificado"

        if not os.path.isabs(caminho):
            caminho = os.path.join(self.diretorio_notas, caminho)

        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)

            if not os.access(os.path.dirname(caminho), os.W_OK):
                return False, "Sem permissão de escrita no diretório"

            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)

            logger.info(f"Nota gravada com sucesso em: {caminho}")
            return True, None

        except Exception as e:
            return False, f"Erro ao gravar nota: {str(e)}"

    def gravar_notas_lote(self, notas: List[Dict]) -> Dict[str, any]:
        """
        Grava um conjunto de notas em lote, retornando estatísticas da operação.

        Args:
            notas (List[Dict]): Lista de dicionários com dados das notas.

        Returns:
            Dict[str, any]: Dicionário com totais, sucessos e mensagens de erro.
        """
        resultado = {
            "sucesso": 0,
            "erros": [],
            "total": len(notas)
        }

        for nota in notas:
            caminho = nota.get('caminho', 'desconhecido')
            try:
                sucesso, erro = self.gravar_nota_individual(nota)

                if sucesso:
                    resultado["sucesso"] += 1
                elif erro:
                    resultado["erros"].append(f"{caminho}: {erro}")

            except Exception as e:
                resultado["erros"].append(f"{caminho}: {str(e)}")

        return resultado

    def guardar_nota_em_caminho(self, nota: Dict, caminho: str) -> Tuple[bool, Optional[str]]:
        """
        Guarda uma nota num caminho personalizado, fora da estrutura padrão.

        Args:
            nota (Dict): Dicionário com conteúdo da nota.
            caminho (str): Caminho absoluto ou relativo para salvar o ficheiro.

        Returns:
            Tuple[bool, Optional[str]]: Sucesso da operação e mensagem de erro (se houver).
        """
        conteudo = nota.get('conteudo', '')

        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)

            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)

            return True, None

        except Exception as e:
            return False, f"Erro ao guardar nota em caminho personalizado: {str(e)}"


# ==============================================================================
# Instância global do gravador
# ==============================================================================

gravador_notas = GravadorNotas()