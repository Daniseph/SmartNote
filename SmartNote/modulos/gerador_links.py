#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: gerador_links.py
Descrição: Módulo responsável por gerar links literais e semânticos entre notas,
           utilizando embeddings e FAISS para avaliação de similaridade contextual.
===============================================================================
"""

import os
import re
import pickle
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import faiss

from modulos.similaridade import SimilaridadeUtils

logger = logging.getLogger(__name__)


# ==============================================================================
# Tentativa de importar dependências avançadas (modelo de linguagem)
# ==============================================================================

try:
    from sentence_transformers import SentenceTransformer
    DEPENDENCIAS_AVANCADAS = True
except ImportError:
    logger.warning("Dependências avançadas não encontradas. Funcionando em modo básico.")
    DEPENDENCIAS_AVANCADAS = False

# ==============================================================================
# Estrutura de Dados: LinkSugerido
# ==============================================================================

@dataclass
class LinkSugerido:
    """
    Representa um link sugerido entre notas.

    Attributes:
        termo (str): Termo ou conceito a ser vinculado.
        nota_destino (str): Título da nota de destino.
        posicao_inicio (int): Índice inicial do termo no texto da nota.
        posicao_fim (int): Índice final do termo no texto da nota.
        score_similaridade (float): Similaridade semântica entre notas.
        contexto (str): Trecho do texto onde o termo aparece.
        tipo (str): Tipo de link ('literal' ou 'semantico').
    """
    termo: str
    nota_destino: str
    posicao_inicio: int
    posicao_fim: int
    score_similaridade: float
    contexto: str
    tipo: str = "semantico"

# ==============================================================================
# Classe Principal: GeradorLinksAvancado
# ==============================================================================

class GeradorLinksAvancado:
    """
    Gerador de links semânticos avançado com embeddings e FAISS.

    Responsável por encontrar relações entre notas, utilizando modelos de linguagem
    para geração de embeddings e índice FAISS para busca por similaridade.
    """

    def __init__(self):
        """
        Inicializa o gerador, definindo os parâmetros padrões e estruturas auxiliares.
        """
        self.modelo_embeddings = None                        # Modelo de geração de embeddings
        self.indice_faiss = None                             # Índice de busca FAISS
        self.mapeamento_notas = {}                           # Mapeamento: ID -> Nota
        self.embeddings_cache = {}                           # Cache local de embeddings
        self.limiar_similaridade = 0.50                      # Valor mínimo para considerar duas notas similares
        self.max_links_por_paragrafo = 3                     # Limite de links por parágrafo
        self.modelo_nome = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
        self.dimensao_embeddings = 384                       # Dimensão do vetor de embedding
        self.cache_path = "cache_embeddings.pkl"             # Caminho para ficheiro de cache
        self.cache_similaridade_termos = {}                  # Cache de similaridade entre termos
        self.stopwords_personalizadas = set()                # Stopwords definidas dinamicamente

    # ==============================================================================
    # Função: encontrar_termo_similar_no_texto
    # ==============================================================================

    def encontrar_termo_similar_no_texto(
        self,
        texto: str,
        termo: str,
        tolerancia: float = 0.80
    ) -> Optional[Tuple[str, int, int, str]]:
        """
        Procura no texto uma expressão semanticamente semelhante ao termo fornecido.

        Utiliza embeddings para comparar o termo com candidatos extraídos de frases do texto.
        Retorna a melhor correspondência com contexto e posição, se satisfizer o limiar
        de similaridade especificado.

        Args:
            texto (str): Texto onde será feita a busca.
            termo (str): Termo original a ser procurado semanticamente.
            tolerancia (float): Limiar mínimo de similaridade para considerar um termo válido.

        Returns:
            Optional[Tuple[str, int, int, str]]: Uma tupla contendo:
                - termo encontrado (str),
                - posição inicial (int),
                - posição final (int),
                - contexto (str),
            ou None caso não encontre similaridade suficiente.
        """
        # Verifica pré-condições mínimas
        if not self.modelo_embeddings or not termo or len(termo) < 3:
            return None

        try:
            # Divide o texto em frases com base em pontuação
            frases = re.split(r'(?<=[.!?])\s+', texto)
            candidatos = []

            # Utiliza NLP para identificar chunks nominais em cada frase
            for frase in frases:
                doc = self.nlp(frase)
                for chunk in doc.noun_chunks:
                    if len(chunk.text.strip()) > 2:
                        candidatos.append((chunk.text.strip(), frase.strip()))

            if not candidatos:
                return None

            # Prepara termos candidatos e gera embeddings
            termos_candidatos = [c[0] for c in candidatos]
            emb_termo = self.modelo_embeddings.encode([termo])
            emb_candidatos = self.modelo_embeddings.encode(termos_candidatos)

            # Compara cada embedding com o termo original
            melhores = []
            for i, emb in enumerate(emb_candidatos):
                score = SimilaridadeUtils.similaridade(emb, emb_termo[0])
                if tolerancia <= score < 0.98:
                    melhores.append((termos_candidatos[i], candidatos[i][1], score))

            if not melhores:
                return None

            # Ordena os candidatos por maior similaridade
            melhor_termo, contexto, _ = sorted(melhores, key=lambda x: -x[2])[0]

            # Localiza posição do termo encontrado no texto original
            match = re.search(rf'\b{re.escape(melhor_termo)}\b', texto, re.IGNORECASE)
            if not match:
                return None

            return melhor_termo, match.start(), match.end(), contexto

        except Exception as e:
            logger.warning(f"Erro ao buscar termo similar: {e}")
            return None
     
    # ==============================================================================
    # Inicialização do modelo e criação do índice FAISS
    # ==============================================================================

    def inicializar_modelo(self) -> bool:
        """
        Inicializa o modelo de embeddings se as dependências estiverem disponíveis.

        Returns:
            bool: True se o modelo for carregado com sucesso, False caso contrário.
        """
        if not DEPENDENCIAS_AVANCADAS:
            logger.warning("Dependências para embeddings não disponíveis")
            return False

        try:
            if self.modelo_embeddings is None:
                logger.info(f"Carregando modelo {self.modelo_nome}...")
                self.modelo_embeddings = SentenceTransformer(self.modelo_nome)
                logger.info("Modelo carregado com sucesso!")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            return False

    def criar_indice_faiss(self, notas: List[Dict]) -> bool:
        """
        Cria um índice FAISS a partir dos embeddings das notas.

        Args:
            notas (List[Dict]): Lista de notas, cada uma contendo 'titulo' e 'conteudo'.

        Returns:
            bool: True se o índice for criado com sucesso, False caso contrário.
        """
        try:
            if not self.inicializar_modelo():
                return False

            logger.info("Criando índice FAISS...")

            # Monta lista de textos e mapeia o índice para a nota original
            textos = []
            self.mapeamento_notas = {}

            for i, nota in enumerate(notas):
                texto = f"{nota['titulo']}\n{nota['conteudo']}"
                textos.append(texto)
                self.mapeamento_notas[i] = nota

            # Geração dos embeddings para todos os textos
            embeddings = self.modelo_embeddings.encode(textos, show_progress_bar=True)
            embeddings = np.array(embeddings).astype('float32')

            # Normaliza os vetores e cria índice FAISS (similaridade cosseno)
            faiss.normalize_L2(embeddings)
            self.indice_faiss = faiss.IndexFlatIP(self.dimensao_embeddings)
            self.indice_faiss.add(embeddings)

            # Salva dados em cache
            self._salvar_cache(embeddings, notas)

            logger.info(f"Índice FAISS criado com {len(notas)} notas")
            return True

        except Exception as e:
            logger.info(f"Erro ao criar índice FAISS: {e}")
            return False

    # ==============================================================================
    # Cache: Salvar Embeddings
    # ==============================================================================

    def _salvar_cache(self, embeddings: np.ndarray, notas: List[Dict]):
        """
        Salva os embeddings e metadados em ficheiro de cache local.

        Args:
            embeddings (np.ndarray): Vetores gerados para cada nota.
            notas (List[Dict]): Lista de dicionários com as notas originais.
        """
        try:
            cache_data = {
                'embeddings': embeddings,
                'mapeamento_notas': self.mapeamento_notas,
                'notas_hash': self._calcular_hash_notas(notas)
            }
            with open(self.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.info(f"Erro ao salvar cache: {e}")

    def _carregar_cache(self, notas: List[Dict]) -> bool:
        """Carrega cache de embeddings se válido."""
        try:
            if not os.path.exists(self.cache_path):
                return False
            
            with open(self.cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verificar se cache é válido
            if cache_data['notas_hash'] != self._calcular_hash_notas(notas):
                return False
            
            # Restaurar dados
            embeddings = cache_data['embeddings']
            self.mapeamento_notas = cache_data['mapeamento_notas']
            
            # Recriar índice FAISS
            self.indice_faiss = faiss.IndexFlatIP(self.dimensao_embeddings)
            self.indice_faiss.add(embeddings)
            
            logger.info("Cache de embeddings carregado com sucesso")
            return True
            
        except Exception as e:
            logger.info(f"Erro ao carregar cache: {e}")
            return False
    
    # ==============================================================================
    # Utilitário: Hash das Notas
    # ==============================================================================

    def _calcular_hash_notas(self, notas: List[Dict]) -> str:
        """
        Calcula um hash MD5 baseado no conteúdo das notas.

        Utilizado para validar se o cache atual ainda é válido ao comparar
        o conteúdo atual com o conteúdo previamente cacheado.

        Args:
            notas (List[Dict]): Lista de notas com 'titulo' e 'conteudo'.

        Returns:
            str: String hash representando o estado atual das notas.
        """
        import hashlib
        conteudo_total = ""

        # Ordena as notas por título para garantir consistência
        for nota in sorted(notas, key=lambda n: n['titulo']):
            conteudo_total += f"{nota['titulo']}{nota['conteudo']}"

        return hashlib.md5(conteudo_total.encode()).hexdigest()

    # ==============================================================================
    # Função: Encontrar Notas Similares com FAISS
    # ==============================================================================

    def encontrar_notas_similares(self, nota_atual: Dict, k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Encontra as k notas mais semanticamente similares à nota atual.

        Utiliza embeddings e índice FAISS para calcular a similaridade entre notas.

        Args:
            nota_atual (Dict): Dicionário com 'titulo' e 'conteudo' da nota a ser comparada.
            k (int): Número de notas similares a retornar (default = 5).

        Returns:
            List[Tuple[Dict, float]]: Lista de tuplas com a nota similar e seu score.
        """
        try:
            # Garante que o modelo e índice estejam disponíveis
            if self.indice_faiss is None or self.modelo_embeddings is None:
                return []

            # Gera embedding da nota atual
            texto_atual = f"{nota_atual['titulo']}\n{nota_atual['conteudo']}"
            embedding_atual = self.modelo_embeddings.encode([texto_atual])
            embedding_atual = np.array(embedding_atual).astype('float32')
            faiss.normalize_L2(embedding_atual)

            # Executa busca no índice FAISS
            scores, indices = self.indice_faiss.search(embedding_atual, k + 1)  # +1 para ignorar a própria nota

            notas_similares = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue  # Índice inválido

                nota_similar = self.mapeamento_notas.get(idx)
                if nota_similar and nota_similar['titulo'] != nota_atual['titulo']:
                    if score >= self.limiar_similaridade:
                        notas_similares.append((nota_similar, float(score)))

            return notas_similares

        except Exception as e:
            logger.info(f"Erro ao encontrar notas similares: {e}")
            return []

    # ==============================================================================
    # Função: Extração de Conceitos Comuns entre Notas
    # ==============================================================================

    def extrair_conceitos_comuns(self, nota1: Dict, nota2: Dict, tolerancia: float = 0.80) -> List[str]:
        """
        Extrai conceitos semanticamente semelhantes entre duas notas.

        Usa embeddings para comparar os termos extraídos de ambas as notas e identifica
        conceitos que possuem alta similaridade semântica.

        Args:
            nota1 (Dict): Primeira nota, contendo pelo menos a chave 'conteudo'.
            nota2 (Dict): Segunda nota, contendo pelo menos a chave 'conteudo'.
            tolerancia (float): Limiar mínimo de similaridade (0.0 a 1.0).

        Returns:
            List[str]: Lista dos conceitos comuns encontrados (limitada a 5).
        """
        try:
            from modulos.conceitos import extrator_conceitos

            # Extrai conceitos relevantes de ambas as notas
            conceitos1 = extrator_conceitos.extrair_conceitos_avancados(nota1['conteudo'])
            conceitos2 = extrator_conceitos.extrair_conceitos_avancados(nota2['conteudo'])

            # Filtra e normaliza termos
            termos1 = [c.termo for c in conceitos1 if len(c.termo) > 2 and c.termo.lower() not in self.stopwords_personalizadas]
            termos2 = [c.termo for c in conceitos2 if len(c.termo) > 2 and c.termo.lower() not in self.stopwords_personalizadas]


            if not termos1 or not termos2 or self.modelo_embeddings is None:
                return []

            # Gera embeddings para os termos das duas notas
            emb1 = self.modelo_embeddings.encode(termos1)
            emb2 = self.modelo_embeddings.encode(termos2)

            conceitos_comuns = set()

            for i, vetor1 in enumerate(emb1):
                for j, vetor2 in enumerate(emb2):
                    chave = tuple(sorted((termos1[i], termos2[j])))

                    # Usa cache para evitar recomputações
                    if chave in self.cache_similaridade_termos:
                        score = self.cache_similaridade_termos[chave]
                    else:
                        score = SimilaridadeUtils.similaridade(vetor1, vetor2)
                        self.cache_similaridade_termos[chave] = score

                    if score >= tolerancia:
                        conceitos_comuns.add(termos1[i])

            return list(conceitos_comuns)[:5]

        except Exception as e:
            logger.info(f"Erro ao extrair conceitos comuns semanticamente: {e}")
            return []

    # ==============================================================================
    # Função: Extração de Contexto por Posição
    # ==============================================================================

    def _extrair_contexto_por_posicao(self, texto: str, posicao: int, margem: int = 100) -> str:
        """
        Extrai uma janela de contexto em torno da posição indicada no texto.

        Args:
            texto (str): Texto de onde será extraído o contexto.
            posicao (int): Posição central de interesse.
            margem (int): Número de caracteres antes e depois a incluir.

        Returns:
            str: Texto de contexto extraído, limpo e com reticências se truncado.
        """
        try:
            inicio = max(0, posicao - margem)
            fim = min(len(texto), posicao + margem)

            contexto = texto[inicio:fim].strip()

            # Remove espaços múltiplos ou quebras de linha
            contexto = re.sub(r'\s+', ' ', contexto)

            # Adiciona reticências para indicar truncamento
            if inicio > 0:
                contexto = "..." + contexto
            if fim < len(texto):
                contexto = contexto + "..."

            return contexto

        except Exception as e:
            logger.warning(f"Erro ao extrair contexto por posição: {e}")
            return ""

    def _normalizar(self, texto: str) -> str:
        """
        Normaliza o texto removendo acentuação e convertendo para minúsculas.

        Útil para comparação de termos de forma uniforme e robusta,
        especialmente em tarefas de pré-processamento de texto.

        Args:
            texto (str): Texto original com ou sem acentuação.

        Returns:
            str: Texto normalizado (sem acentos, em lowercase).
        """
        import unicodedata
        texto = unicodedata.normalize('NFKD', texto)
        texto = ''.join(c for c in texto if not unicodedata.combining(c))
        return texto.lower()

    # ==============================================================================
    # Função: Gerar Sugestões de Links entre Notas
    # ==============================================================================

    def gerar_sugestoes_links(
        self,
        nota_atual: Dict,
        notas_similares: List[Tuple[Dict, float]]
    ) -> List[LinkSugerido]:
        """
        Gera sugestões de links entre a nota atual e outras notas semanticamente similares.

        O processo considera conceitos comuns entre notas, tentando primeiro encontrar
        uma ocorrência literal do conceito. Se não encontrado, tenta uma correspondência
        semântica aproximada. Cada sugestão inclui posição e contexto, se disponível.

        Args:
            nota_atual (Dict): Nota em análise (com campos 'titulo' e 'conteudo').
            notas_similares (List[Tuple[Dict, float]]): Lista de notas semelhantes com score.

        Returns:
            List[LinkSugerido]: Lista de sugestões de links, limitadas por parágrafo e tipo.
        """
        sugestoes = []
        sugestoes_existentes = set()
        conteudo = nota_atual.get('conteudo', '')
        paragrafos = re.split(r'\n\s*\n', conteudo)  # Divide por parágrafos (linhas em branco)

        for nota_similar, score in notas_similares:
            conceitos_comuns = self.extrair_conceitos_comuns(nota_atual, nota_similar)

            for conceito in conceitos_comuns:
                chave = (conceito.lower(), nota_similar['titulo'].lower())
                if chave in sugestoes_existentes:
                    continue  # Evita duplicação

                termo_encontrado = False

                # ----------------------------------------------------------------------
                # Busca Literal: tenta localizar o conceito diretamente nos parágrafos
                # ----------------------------------------------------------------------
                for i, paragrafo in enumerate(paragrafos):
                    if conceito.lower() in paragrafo.lower():
                        match = re.search(rf'\b{re.escape(conceito)}\b', paragrafo, re.IGNORECASE)
                        if match:
                            pos_paragrafo = sum(len(p) + 2 for p in paragrafos[:i])  # posição no texto completo
                            sugestoes.append(LinkSugerido(
                                termo=conceito,
                                nota_destino=nota_similar['titulo'],
                                posicao_inicio=pos_paragrafo + match.start(),
                                posicao_fim=pos_paragrafo + match.end(),
                                score_similaridade=score,
                                contexto=paragrafo.strip(),
                                tipo="literal"
                            ))
                            termo_encontrado = True
                            break

                # ----------------------------------------------------------------------
                # Fallback Semântico: tenta encontrar termo equivalente se literal falhar
                # ----------------------------------------------------------------------
                if not termo_encontrado:
                    resultado = self.encontrar_termo_similar_no_texto(conteudo, conceito)
                    if resultado:
                        termo_similar, pos_inicio, pos_fim, contexto = resultado
                        sugestoes.append(LinkSugerido(
                            termo=termo_similar,
                            nota_destino=nota_similar['titulo'],
                            posicao_inicio=pos_inicio,
                            posicao_fim=pos_fim,
                            score_similaridade=score,
                            contexto=contexto,
                            tipo="semantico"
                        ))
                    else:
                        # Caso não encontre posição exata, registra como semântico indireto
                        sugestoes.append(LinkSugerido(
                            termo=conceito,
                            nota_destino=nota_similar['titulo'],
                            posicao_inicio=-1,
                            posicao_fim=-1,
                            score_similaridade=score,
                            contexto=f"(semântico) Conceito relacionado: {conceito}",
                            tipo="semantico"
                        ))

                sugestoes_existentes.add(chave)

        # --------------------------------------------------------------------------
        # Limita visualmente os links semânticos (controle de UX/UI)
        # --------------------------------------------------------------------------
        literais = [s for s in sugestoes if s.tipo == 'literal']
        semanticos = [s for s in sugestoes if s.tipo == 'semantico']
        max_semanticos = 5  # pode ser configurado externamente se necessário

        return literais + semanticos[:max_semanticos]

    # ==============================================================================
    # Funções Auxiliares: Stopwords Personalizadas e Filtro por Parágrafo
    # ==============================================================================

    def atualizar_stopwords_personalizadas(self, lista: List[str]):
        """
        Atualiza a lista de stopwords personalizadas em tempo de execução.

        Permite adaptar dinamicamente o comportamento do filtro de termos irrelevantes
        com base no contexto específico do utilizador ou domínio.

        Args:
            lista (List[str]): Lista de termos a serem tratados como stopwords.
        """
        self.stopwords_personalizadas = set(lista)

    def _filtrar_por_paragrafo(self, sugestoes: List[LinkSugerido], conteudo: str) -> List[LinkSugerido]:
        """
        Filtra sugestões de links para respeitar o limite máximo por parágrafo.

        Dá prioridade aos links literais e preenche o restante com sugestões semânticas,
        respeitando o número máximo configurado (`self.max_links_por_paragrafo`).

        Args:
            sugestoes (List[LinkSugerido]): Lista de todas as sugestões geradas.
            conteudo (str): Texto completo da nota (dividido por parágrafos).

        Returns:
            List[LinkSugerido]: Lista final filtrada, pronta para exibição/aplicação.
        """
        paragrafos = conteudo.split('\n\n')  # Divide conteúdo por parágrafos
        sugestoes_filtradas = []

        for i, paragrafo in enumerate(paragrafos):
            pos_paragrafo = sum(len(p) + 2 for p in paragrafos[:i])  # Posição de início do parágrafo
            pos_fim_paragrafo = pos_paragrafo + len(paragrafo)

            # Seleciona sugestões localizadas dentro deste parágrafo
            sugestoes_paragrafo = [
                s for s in sugestoes 
                if pos_paragrafo <= s.posicao_inicio < pos_fim_paragrafo
            ]

            # Separa por tipo
            literais = [s for s in sugestoes_paragrafo if s.tipo == 'literal']
            semanticos = [s for s in sugestoes_paragrafo if s.tipo == 'semantico']

            # Ordena por score decrescente
            literais.sort(key=lambda s: s.score_similaridade, reverse=True)
            semanticos.sort(key=lambda s: s.score_similaridade, reverse=True)

            # Adiciona até o máximo permitido por parágrafo
            sugestoes_filtradas.extend(literais[:self.max_links_por_paragrafo])

            if len(literais) < self.max_links_por_paragrafo:
                restante = self.max_links_por_paragrafo - len(literais)
                sugestoes_filtradas.extend(semanticos[:restante])

        return sugestoes_filtradas
    
    # ==============================================================================
    # Função: Processar Nota para Geração de Links
    # ==============================================================================

    def processar_nota_para_links(self, nota: Dict, todas_notas: List[Dict]) -> List[LinkSugerido]:
        """
        Processa uma nota para gerar sugestões de links (semânticos e literais).

        Verifica se o modo semântico está ativado, garante a existência do índice FAISS,
        encontra notas semelhantes e gera sugestões relevantes com base em conceitos comuns.

        Args:
            nota (Dict): Nota atual que está sendo editada ou criada.
            todas_notas (List[Dict]): Conjunto de todas as notas disponíveis.

        Returns:
            List[LinkSugerido]: Lista de sugestões geradas para a nota.
        """
        sugestoes = []

        if not getattr(self, "modo_semantico", True):
            logger.info("Modo semântico desativado — ignorando geração de links automáticos.")
            return sugestoes

        try:
            # Garante que o índice FAISS está carregado
            if self.indice_faiss is None:
                if not self._carregar_cache(todas_notas):
                    if not self.criar_indice_faiss(todas_notas):
                        return []

            # Obtém notas similares
            notas_similares = self.encontrar_notas_similares(nota)
            if not notas_similares:
                return []

            # Gera sugestões de links
            sugestoes = self.gerar_sugestoes_links(nota, notas_similares)

            return sugestoes

        except Exception as e:
            logger.info(f"Erro ao processar nota para links: {e}")
            return []

    # ==============================================================================
    # Função: Remover Sugestões Duplicadas
    # ==============================================================================

    @staticmethod
    def filtrar_sugestoes_duplicadas(sugestoes: List[LinkSugerido]) -> List[LinkSugerido]:
        """
        Remove sugestões de links duplicadas com base em termo e nota de destino.

        Args:
            sugestoes (List[LinkSugerido]): Lista de sugestões possivelmente redundantes.

        Returns:
            List[LinkSugerido]: Lista filtrada e sem duplicações.
        """
        vistos = set()
        filtrados = []
        for s in sugestoes:
            chave = (s.termo.lower(), s.nota_destino)
            if chave in vistos:
                continue
            vistos.add(chave)
            filtrados.append(s)
        return filtrados

    # ==============================================================================
    # Função: Configurar Parâmetros de Similaridade e Limite por Parágrafo
    # ==============================================================================

    def configurar_parametros(self, limiar_similaridade: float = 0.15, max_links_por_paragrafo: int = 3):
        """
        Atualiza os parâmetros de funcionamento do gerador de links.

        Args:
            limiar_similaridade (float): Valor mínimo de similaridade para sugerir links.
            max_links_por_paragrafo (int): Número máximo de links permitidos por parágrafo.
        """
        self.limiar_similaridade = limiar_similaridade
        self.max_links_por_paragrafo = max_links_por_paragrafo


# ==============================================================================
# Instância Global do Gerador
# ==============================================================================

gerador_links_avancado = GeradorLinksAvancado()
