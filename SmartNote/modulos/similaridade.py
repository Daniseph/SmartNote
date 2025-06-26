#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: similaridade.py
Descrição: Utilitário para cálculo de similaridade vetorial entre embeddings,
           usando similaridade do cosseno.
===============================================================================
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ==============================================================================
# Classe utilitária de similaridade
# ==============================================================================


class SimilaridadeUtils:
    """
    Classe utilitária para cálculo de similaridade entre vetores
    usando a métrica do cosseno.
    """

    @staticmethod
    def similaridade(v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Calcula a similaridade do cosseno entre dois vetores.

        Args:
            v1 (np.ndarray): Vetor 1 (embedding), unidimensional ou matriz.
            v2 (np.ndarray): Vetor 2 (embedding), unidimensional ou matriz.

        Returns:
            float: Similaridade do cosseno (valor entre -1 e 1), arredondado a 4 casas decimais.
        """
        if v1.ndim == 1:
            v1 = v1.reshape(1, -1)
        if v2.ndim == 1:
            v2 = v2.reshape(1, -1)

        score = cosine_similarity(v1, v2)[0][0]
        return round(float(score), 4)