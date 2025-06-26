#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: importacao.py
Descrição: Módulo de importação de notas a partir de ficheiros locais (.md, .txt).
           Suporta extração automática de metadados no formato YAML (frontmatter),
           quando presentes no início do ficheiro.
===============================================================================
"""

import os
import yaml
import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NotaImportada:
    """
    Estrutura que representa uma nota importada de um ficheiro.

    Attributes:
        titulo (str): Nome do ficheiro sem extensão.
        conteudo (str): Conteúdo textual da nota.
        caminho (str): Caminho completo do ficheiro.
        frontmatter (Dict): Metadados extraídos em formato YAML.
        tamanho (int): Tamanho do ficheiro em bytes.
        data_modificacao (datetime): Data de modificação do ficheiro.
        valida (bool): Indica se a nota foi importada com sucesso.
        erro (Optional[str]): Mensagem de erro, se aplicável.
    """
    titulo: str
    conteudo: str
    caminho: str
    frontmatter: Dict
    tamanho: int
    data_modificacao: datetime
    valida: bool
    erro: Optional[str] = None

def _conteudo_legivel(texto: str) -> bool:
    """
    Verifica se o conteúdo é predominantemente legível com base em amostragem.

    Args:
        texto (str): Texto a ser avaliado.

    Returns:
        bool: True se pelo menos 90% dos primeiros 100 caracteres forem imprimíveis.
    """
    amostra = texto[:100]
    legiveis = sum(c.isprintable() or c.isspace() for c in amostra)
    return (len(amostra) == 0) or (legiveis / len(amostra) >= 0.9)



def importar_diretorio(caminho_base: str) -> Tuple[List[NotaImportada], List[str]]:
    """
    Importa notas de um diretório local, processando ficheiros .md, .txt e similares.

    Lê conteúdo, extrai frontmatter (YAML), valida legibilidade e trata diferentes codificações.

    Args:
        caminho_base (str): Caminho para o diretório com as notas.

    Returns:
        Tuple[List[NotaImportada], List[str]]: Lista de notas válidas ou com erro,
                                               e lista de mensagens de erro.
    """
    notas = []
    erros = []

    extensoes_validas = {'.md', '.markdown', '.txt'}
    codificacoes = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

    if not os.path.isdir(caminho_base):
        return [], [f"Diretório inválido: {caminho_base}"]

    for nome_ficheiro in os.listdir(caminho_base):
        caminho = os.path.join(caminho_base, nome_ficheiro)

        if os.path.isfile(caminho):
            _, ext = os.path.splitext(nome_ficheiro.lower())
            if ext in extensoes_validas:
                try:
                    stat = os.stat(caminho)
                except Exception as e:
                    erros.append(f"{nome_ficheiro}: Erro ao acessar o arquivo - {e}")
                    continue

                conteudo = None
                for cod in codificacoes:
                    try:
                        with open(caminho, 'r', encoding=cod) as f:
                            conteudo = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    notas.append(NotaImportada(
                        titulo=os.path.splitext(nome_ficheiro)[0],
                        conteudo="",
                        caminho=caminho,
                        frontmatter={},
                        tamanho=stat.st_size,
                        data_modificacao=datetime.fromtimestamp(stat.st_mtime),
                        valida=False,
                        erro="Erro de codificação"
                    ))
                    erros.append(f"{nome_ficheiro}: Erro de codificação.")
                    continue

                if not _conteudo_legivel(conteudo):
                    notas.append(NotaImportada(
                        titulo=os.path.splitext(nome_ficheiro)[0],
                        conteudo=conteudo,
                        caminho=caminho,
                        frontmatter={},
                        tamanho=stat.st_size,
                        data_modificacao=datetime.fromtimestamp(stat.st_mtime),
                        valida=False,
                        erro="Conteúdo ilegível"
                    ))
                    erros.append(f"{nome_ficheiro}: Conteúdo ilegível.")
                    continue

                frontmatter = {}
                match = re.match(r'^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)', conteudo, re.DOTALL)
                if match:
                    try:
                        frontmatter = yaml.safe_load(match.group(1)) or {}
                        conteudo = match.group(2)
                    except Exception as e:
                        logger.warning(f"{nome_ficheiro}: Erro ao processar frontmatter - {e}")

                try:
                    notas.append(NotaImportada(
                        titulo=os.path.splitext(nome_ficheiro)[0],
                        conteudo=conteudo,
                        caminho=caminho,
                        frontmatter=frontmatter,
                        tamanho=stat.st_size,
                        data_modificacao=datetime.fromtimestamp(stat.st_mtime),
                        valida=True
                    ))
                except Exception as e:
                    erros.append(f"{nome_ficheiro}: Erro ao processar nota - {e}")

    return notas, erros
