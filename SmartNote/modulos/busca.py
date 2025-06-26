#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: busca.py
Descrição: Módulo de busca textual e por regex nas notas, com suporte a acentos,
           caixa, cache e ordenação por score.
===============================================================================
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Dict, Any


# ==============================================================================
# Estrutura de Dados
# ==============================================================================

@dataclass
class ResultadoBusca:
    titulo: str
    caminho: str
    trecho: str
    posicoes: List[int]
    score: float

# ==============================================================================
# Classe Principal de Busca
# ==============================================================================

class Buscador:
    """
    Classe de busca textual configurável com cache, regex, acentos e caixa.
    """

    def __init__(self):
        self.cache = {}

    def configurar_busca(self, termo: str, configuracao: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara os parâmetros de busca de acordo com as opções fornecidas.

        Args:
            termo (str): Termo original de busca.
            configuracao (Dict): Opções da busca.

        Returns:
            Dict: Parâmetros tratados para uso interno.
        """
        termo_original = termo

        if configuracao.get("ignorar_acentos"):
            termo = self._remover_acentos(termo)

        if not configuracao.get("diferenciar_maiusculas"):
            termo = termo.lower()

        return {
            "termo": termo,
            "original": termo_original,
            "regex": configuracao.get("modo_regex", False),
            "cache": configuracao.get("usar_cache", False),
            "ignorar_acentos": configuracao.get("ignorar_acentos", True),
            "diferenciar_maiusculas": configuracao.get("diferenciar_maiusculas", False)
        }

    def buscar(self, termo: str, notas: List[Dict[str, Any]], configuracao: Dict[str, Any]) -> List[ResultadoBusca]:
        """
        Executa a busca textual ou regex sobre o conteúdo das notas.

        Args:
            termo (str): Termo de busca.
            notas (List[Dict]): Lista de notas.
            configuracao (Dict): Parâmetros de configuração da busca.

        Returns:
            List[ResultadoBusca]: Resultados ordenados por score.
        """
        cfg = self.configurar_busca(termo, configuracao)
        chave_cache = f"{cfg['termo']}_{cfg['regex']}_{cfg['ignorar_acentos']}_{cfg['diferenciar_maiusculas']}"

        if cfg["cache"] and chave_cache in self.cache:
            return self.cache[chave_cache]

        resultados = []

        for nota in notas:
            conteudo = nota.get("conteudo", "")
            texto_original = conteudo

            if cfg["ignorar_acentos"]:
                conteudo = self._remover_acentos(conteudo)

            if not cfg["diferenciar_maiusculas"]:
                conteudo = conteudo.lower()

            if cfg["regex"]:
                ocorrencias = [m.start() for m in re.finditer(cfg["termo"], conteudo)]
            else:
                ocorrencias = [m.start() for m in re.finditer(re.escape(cfg["termo"]), conteudo)]

            if ocorrencias:
                score = self._calcular_score(nota, cfg["termo"], ocorrencias)
                trecho = self._extrair_trecho(texto_original, ocorrencias[0])
                resultados.append(ResultadoBusca(
                    titulo=nota.get("titulo", ""),
                    caminho=nota.get("caminho", ""),
                    trecho=trecho,
                    posicoes=ocorrencias,
                    score=score
                ))

        resultados.sort(key=lambda r: r.score, reverse=True)

        if cfg["cache"]:
            self.cache[chave_cache] = resultados

        return resultados

    def _remover_acentos(self, texto: str) -> str:
        """
        Remove acentos do texto.

        Args:
            texto (str): Texto original.

        Returns:
            str: Texto sem acentos.
        """
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def _extrair_trecho(self, texto: str, pos: int, margem: int = 30) -> str:
        """
        Extrai um trecho do texto ao redor da ocorrência.

        Args:
            texto (str): Texto original.
            pos (int): Posição da ocorrência.
            margem (int): Quantidade de caracteres antes e depois.

        Returns:
            str: Trecho extraído.
        """
        inicio = max(pos - margem, 0)
        fim = min(pos + margem, len(texto))
        return texto[inicio:fim].replace('\n', ' ')


    def _calcular_score(self, nota: Dict[str, Any], termo: str, ocorrencias: List[int]) -> float:
        """
        Calcula score de relevância com base na posição e frequência.

        Args:
            nota (Dict): Dados da nota.
            termo (str): Termo buscado.
            ocorrencias (List[int]): Posições encontradas.

        Returns:
            float: Score da nota.
        """
        score = 0
        titulo = nota.get("titulo", "")

        if termo.lower() in titulo.lower():
            score += 2

        if ocorrencias and ocorrencias[0] < 50:
            score += 1

        score += len(ocorrencias) * 0.5
        return score

# ==============================================================================
# Interface de Uso Externo
# ==============================================================================

buscador_textual = Buscador()

def buscar(termo: str, notas: List[Dict[str, Any]], configuracao: Dict[str, Any] = None) -> List[ResultadoBusca]:
    """
    Executa busca em notas com base nas opções fornecidas.

    Args:
        termo (str): Termo de busca.
        notas (List[Dict]): Lista de notas.
        configuracao (Dict): Parâmetros como:
            - ignorar_acentos (bool)
            - diferenciar_maiusculas (bool)
            - modo_regex (bool)
            - usar_cache (bool)

    Returns:
        List[ResultadoBusca]: Lista de resultados ordenados.
    """
    if not isinstance(termo, str) or not termo.strip():
        return []

    if not isinstance(notas, list):
        raise ValueError("A lista de notas deve ser uma lista de dicionários.")

    if configuracao is None:
        configuracao = {}

    try:
        return buscador_textual.buscar(termo, notas, configuracao)
    except Exception as e:
        return []
