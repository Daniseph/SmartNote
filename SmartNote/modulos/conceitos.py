#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: conceitos.py
Descrição: Módulo de extração avançada de conceitos com suporte a NLP via spaCy.
===============================================================================
"""

import re
import logging
from typing import List, Dict, Set, Optional
from collections import Counter
from dataclasses import dataclass, field
from modulos.configuracao import configurador

logger = logging.getLogger(__name__)


# ==============================================================================
# Verificação de Dependências Externas (spaCy)
# ==============================================================================

try:
    import spacy
    SPACY_DISPONIVEL = True
except ImportError:
    logger.warning("spaCy não disponível. Usando extração básica de conceitos.")
    SPACY_DISPONIVEL = False

# ==============================================================================
# Estrutura de Dados
# ==============================================================================

@dataclass
class Conceito:
    """
    Representa um conceito identificado a partir de texto.

    Attributes:
        termo (str): Termo principal do conceito.
        frequencia (int): Número de ocorrências.
        pos_tag (str): Categoria gramatical (parte do discurso).
        relevancia (float): Score de importância relativa.
        contextos (List[str]): Frases onde o conceito foi encontrado.
        tipo (Optional[str]): Categoria semântica, se aplicável.
    """
    termo: str
    frequencia: int
    pos_tag: str
    relevancia: float
    contextos: List[str]
    tipo: Optional[str] = field(default=None)


class ExtratorConceitos:
    """
    Extrator de conceitos utilizando análise linguística com spaCy.
    Permite cache e integração com stopwords personalizadas.
    """

    def __init__(self, modelo_spacy: str = 'pt_core_news_sm'):
        """
        Inicializa o extrator com o modelo linguístico desejado.

        Args:
            modelo_spacy (str): Nome do modelo spaCy a carregar.
        """
        self.nlp = None

        if SPACY_DISPONIVEL:
            try:
                self.nlp = spacy.load(modelo_spacy)
                logger.info(f"Modelo spaCy '{modelo_spacy}' carregado com sucesso.")
            except OSError:
                logger.warning(f"Modelo '{modelo_spacy}' não encontrado. Extração ativada.")

        self.cache_conceitos: Dict[str, List[Conceito]] = {}
        self.stopwords_personalizadas: Set[str] = set()

        self._carregar_stopwords_padrao()
        self.adicionar_stopwords(configurador.obter_stopwords_personalizadas())

    
    # ==============================================================================
    # Métodos: Carregamento e Gestão de Stopwords
    # ==============================================================================

    def _carregar_stopwords_padrao(self):
        """
        Inicializa a lista de stopwords padrão utilizadas para filtrar termos genéricos.
        """
        self.stopwords_personalizadas.update([
            'coisa', 'algo', 'alguém', 'pessoa',
            'forma', 'modo', 'tipo', 'exemplo', 'caso', 'situação',
            'hoje', 'ontem', 'amanhã', 'agora', 'depois', 'antes',
            'momento', 'tempo', 'vez',
            'muito', 'pouco', 'algum', 'todo',
            'lugar', 'local', 'área', 'parte'
        ])

    def adicionar_stopwords(self, palavras: List[str]):
        """
        Adiciona uma lista de palavras à lista de stopwords personalizadas.

        Args:
            palavras (List[str]): Lista de palavras a ignorar durante a extração.
        """
        self.stopwords_personalizadas.update(palavra.lower() for palavra in palavras)

    # ==============================================================================
    # Extração Avançada de Conceitos
    # ==============================================================================

    def extrair_conceitos_avancados(self, texto: str, titulo_nota: str = "") -> List[Conceito]:
        """
        Extrai conceitos relevantes de um texto utilizando múltiplas estratégias linguísticas.

        Args:
            texto (str): Texto base de onde extrair os conceitos.
            titulo_nota (str, optional): Título da nota, usado para caching.

        Returns:
            List[Conceito]: Lista de conceitos extraídos com metadados.
        """
        if not texto or not self.nlp:
            return []

        cache_key = hash(texto + titulo_nota)
        if cache_key in self.cache_conceitos:
            return self.cache_conceitos[cache_key]

        conceitos: List[Conceito] = []
        conceitos.extend(self._extrair_entidades_nomeadas(texto))
        conceitos.extend(self._extrair_substantivos_compostos(texto))
        conceitos.extend(self._extrair_termos_tecnicos(texto))
        conceitos.extend(self._extrair_por_frequencia(texto))

        conceitos_filtrados = self._filtrar_e_consolidar(conceitos, texto)
        self.cache_conceitos[cache_key] = conceitos_filtrados

        return conceitos_filtrados


    def _extrair_entidades_nomeadas(self, texto: str) -> List[Conceito]:
        """
        Utiliza NER (Named Entity Recognition) do spaCy para extrair entidades com alta relevância.

        Args:
            texto (str): Texto de origem.

        Returns:
            List[Conceito]: Lista de conceitos baseados em entidades.
        """
        conceitos = []
        doc = self.nlp(texto)

        for ent in doc.ents:
            if len(ent.text.strip()) > 2 and ent.label_ in {'PERSON', 'ORG', 'GPE', 'PRODUCT'}:
                termo_limpo = self._limpar_termo(ent.text)
                if termo_limpo and self._validar_conceito(termo_limpo):
                    conceitos.append(Conceito(
                        termo=termo_limpo,
                        frequencia=1,
                        pos_tag=ent.label_,
                        relevancia=0.9,
                        contextos=[ent.sent.text[:100]]
                    ))

        return conceitos
    
    # ==============================================================================
    # Métodos: Extração de Substantivos Compostos e Termos Técnicos
    # ==============================================================================

    def _extrair_substantivos_compostos(self, texto: str) -> List[Conceito]:
        """
        Extrai substantivos compostos a partir da análise de dependência sintática.

        Args:
            texto (str): Texto alvo da análise.

        Returns:
            List[Conceito]: Lista de conceitos compostos encontrados.
        """
        conceitos = []
        doc = self.nlp(texto)

        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN']:
                termos = []

                for filho in token.lefts:
                    if filho.dep_ in ['amod', 'compound', 'nmod'] and filho.pos_ in ['NOUN', 'ADJ', 'PROPN']:
                        termos.append(filho.text)

                termos.append(token.text)

                for filho in token.rights:
                    if filho.dep_ == 'nmod' and filho.pos_ in ['NOUN', 'PROPN']:
                        termos.append(filho.text)

                termo_composto = " ".join(termos)
                termo_limpo = self._limpar_termo(termo_composto)

                if termo_limpo and self._validar_conceito(termo_limpo):
                    conceitos.append(Conceito(
                        termo=termo_limpo,
                        frequencia=1,
                        pos_tag='COMPOUND_NOUN',
                        relevancia=0.8,
                        contextos=[token.sent.text[:100]]
                    ))

        return conceitos


    def _expandir_termo_composto(self, doc, inicio: int) -> str:
        """
        Expande um termo composto a partir de um índice no documento spaCy.

        Args:
            doc (spacy.tokens.Doc): Documento processado pelo spaCy.
            inicio (int): Índice inicial do termo.

        Returns:
            str: Termo composto, se encontrado.
        """
        termos = []
        i = inicio

        while (
            i < len(doc) and
            doc[i].pos_ in ['NOUN', 'PROPN', 'ADJ'] and
            not doc[i].is_stop and doc[i].is_alpha and
            len(termos) < 4
        ):
            termos.append(doc[i].text)
            i += 1

        return ' '.join(termos) if len(termos) >= 2 else ''


    def _extrair_termos_tecnicos(self, texto: str) -> List[Conceito]:
        """
        Extrai termos técnicos como siglas e palavras com hífen ou underscore.

        Args:
            texto (str): Texto alvo da análise.

        Returns:
            List[Conceito]: Lista de conceitos técnicos extraídos.
        """
        conceitos = []

        # Extrair siglas (2 a 5 letras maiúsculas)
        padrao_siglas = r'\b[A-Z]{2,5}\b'
        siglas = re.findall(padrao_siglas, texto)

        for sigla in set(siglas):
            if self._validar_conceito(sigla):
                freq = texto.count(sigla)
                conceitos.append(Conceito(
                    termo=sigla,
                    frequencia=freq,
                    pos_tag='ACRONYM',
                    relevancia=0.7,
                    contextos=self._extrair_contextos(texto, sigla)
                ))

        # Extrair termos com hífen ou underscore
        padrao_tecnicos = r'\b\w+[-_]\w+(?:[-_]\w+)*\b'
        termos_tecnicos = re.findall(padrao_tecnicos, texto)

        for termo in set(termos_tecnicos):
            if self._validar_conceito(termo):
                freq = texto.count(termo)
                conceitos.append(Conceito(
                    termo=termo,
                    frequencia=freq,
                    pos_tag='TECHNICAL',
                    relevancia=0.6,
                    contextos=self._extrair_contextos(texto, termo)
                ))

        return conceitos


    # ==============================================================================
    # Métodos: Extração Baseada em Frequência e Utilitários de Validação
    # ==============================================================================

    def _extrair_por_frequencia(self, texto: str) -> List[Conceito]:
        """
        Extrai conceitos com base na frequência de ocorrência de termos compostos e substantivos.

        Args:
            texto (str): Texto completo da nota.

        Returns:
            List[Conceito]: Lista de conceitos extraídos com frequência significativa.
        """
        conceitos = []
        doc = self.nlp(texto)
        contador_termos = Counter()

        # 1. Extração com noun_chunks
        for chunk in doc.noun_chunks:
            termo = chunk.text.lower().strip()
            termo_limpo = self._limpar_termo(termo)
            if termo_limpo and self._validar_conceito(termo_limpo):
                contador_termos[termo_limpo] += 1

        # 2. Fallback para palavras individuais
        for token in doc:
            if (
                token.pos_ in ['NOUN', 'PROPN'] and
                len(token.text) > 3 and
                not token.is_stop and
                token.is_alpha
            ):
                termo_limpo = self._limpar_termo(token.lemma_)
                if termo_limpo and self._validar_conceito(termo_limpo):
                    contador_termos[termo_limpo] += 1

        # 3. Converter para objetos Conceito
        for termo, freq in contador_termos.items():
            if freq >= 2:
                relevancia = min(0.5 + (freq * 0.1), 1.0)
                conceitos.append(Conceito(
                    termo=termo,
                    frequencia=freq,
                    pos_tag='NOUN',
                    relevancia=relevancia,
                    contextos=self._extrair_contextos(texto, termo)
                ))

        return conceitos


    # ==============================================================================
    # Métodos Auxiliares de Limpeza, Validação e Contexto
    # ==============================================================================

    def _limpar_termo(self, termo: str) -> str:
        """
        Limpa e normaliza um termo extraído do texto.

        Args:
            termo (str): Termo bruto extraído.

        Returns:
            str: Termo normalizado e em lowercase.
        """
        termo_limpo = re.sub(r'[^\w\s-]', '', termo).strip()
        termo_limpo = re.sub(r'\s+', ' ', termo_limpo)
        return termo_limpo.lower()

    def _validar_conceito(self, termo: str) -> bool:
        """
        Verifica se um termo é um conceito válido, excluindo stopwords, números e termos triviais.

        Args:
            termo (str): Termo a validar.

        Returns:
            bool: True se for válido, False caso contrário.
        """
        if not termo or len(termo) < 3:
            return False
        if termo.lower() in self.stopwords_personalizadas:
            return False
        if termo.isdigit():
            return False
        if not any(c.isalpha() for c in termo):
            return False
        return True

    def _extrair_contextos(self, texto: str, termo: str, max_contextos: int = 3) -> List[str]:
        """
        Extrai frases curtas onde o termo aparece no texto, limitando a três ocorrências.

        Args:
            texto (str): Texto completo.
            termo (str): Termo para busca.
            max_contextos (int): Número máximo de contextos a extrair.

        Returns:
            List[str]: Lista de frases parciais com o termo.
        """
        contextos = []
        frases = re.split(r'[.!?]+', texto)

        for frase in frases:
            if re.search(rf'(?<!\w){re.escape(termo)}(?!\w)', frase, re.IGNORECASE):
                contexto = frase.strip()[:100]
                if contexto:
                    contextos.append(contexto)
            if len(contextos) >= max_contextos:
                break

        return contextos

    
    # ==============================================================================
    # Métodos: Consolidação de Conceitos e Extração Básica (Fallback)
    # ==============================================================================

    def _filtrar_e_consolidar(self, conceitos: List[Conceito], texto: str) -> List[Conceito]:
        """
        Consolida conceitos duplicados com base no termo, agregando frequência, contexto e relevância.

        Args:
            conceitos (List[Conceito]): Lista de conceitos brutos.
            texto (str): Texto original (para contexto).

        Returns:
            List[Conceito]: Lista consolidada e ordenada dos conceitos principais.
        """
        grupos_conceitos = {}
        for conceito in conceitos:
            termo = conceito.termo
            grupos_conceitos.setdefault(termo, []).append(conceito)

        conceitos_consolidados = []
        for termo, grupo in grupos_conceitos.items():
            if len(grupo) == 1:
                conceitos_consolidados.append(grupo[0])
            else:
                freq_total = sum(c.frequencia for c in grupo)
                relevancia_max = max(c.relevancia for c in grupo)
                pos_tag_melhor = max(grupo, key=lambda c: c.relevancia).pos_tag
                contextos_todos = []
                for c in grupo:
                    contextos_todos.extend(c.contextos)

                conceitos_consolidados.append(Conceito(
                    termo=termo,
                    frequencia=freq_total,
                    pos_tag=pos_tag_melhor,
                    relevancia=relevancia_max,
                    contextos=list(set(contextos_todos))[:3]
                ))

        conceitos_consolidados.sort(key=lambda c: (c.relevancia, c.frequencia), reverse=True)
        return conceitos_consolidados[:20]


    def limpar_cache(self):
        """
        Limpa o cache de conceitos armazenados.
        """
        self.cache_conceitos.clear()


    def extrair_conceitos_basicos(self, texto: str) -> List[Conceito]:
        """
        Extrai conceitos básicos usando regex, frequência e filtros simples.

        Usado como fallback quando spaCy não está disponível.

        Args:
            texto (str): Texto da nota.

        Returns:
            List[Conceito]: Lista reduzida de conceitos principais.
        """
        if not texto:
            return []

        conceitos = []

        # 1. Extração de palavras significativas
        palavras = re.findall(r'\b[A-Za-zÀ-ÿ]{3,}\b', texto)
        contador = Counter(p.lower() for p in palavras)

        # 2. Conceitos por frequência e validação
        for palavra, freq in contador.items():
            if (
                freq >= 1 and
                self._validar_conceito(palavra) and
                palavra not in self.stopwords_personalizadas
            ):
                relevancia = min(0.3 + (freq * 0.1), 1.0)
                conceitos.append(Conceito(
                    termo=palavra,
                    frequencia=freq,
                    pos_tag='WORD',
                    relevancia=relevancia,
                    contextos=self._extrair_contextos(texto, palavra)
                ))

        # 3. Siglas e termos técnicos (acréscimo opcional)
        siglas = re.findall(r'\b[A-Z]{2,5}\b', texto)
        for sigla in set(siglas):
            if self._validar_conceito(sigla):
                freq = texto.count(sigla)
                conceitos.append(Conceito(
                    termo=sigla,
                    frequencia=freq,
                    pos_tag='ACRONYM',
                    relevancia=0.7,
                    contextos=self._extrair_contextos(texto, sigla)
                ))

        conceitos.sort(key=lambda c: (c.relevancia, c.frequencia), reverse=True)
        return conceitos[:15]  # Máximo de 15 conceitos básicos


# ==============================================================================
# Instância Global
# ==============================================================================

extrator_conceitos = ExtratorConceitos()
