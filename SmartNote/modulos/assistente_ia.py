#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: assistente_ia.py
Descrição: Sistema de assistente IA com RAG melhorado para o SmartNote.
           Implementa RAG offline com indexação FAISS e integração Ollama.
===============================================================================
"""

import logging
import requests
from dataclasses import dataclass
from typing import List, Dict
from modulos.configuracao import configurador


logger = logging.getLogger(__name__)

# ==============================================================================
# Dependências Opcionais (FAISS, embeddings)
# ==============================================================================

try:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    DEPENDENCIAS_AVANCADAS = True
except ImportError:
    logger.warning("Dependências avançadas não encontradas. Funcionando em modo básico.")
    DEPENDENCIAS_AVANCADAS = False

# ==============================================================================
# Estruturas de Dados
# ==============================================================================

@dataclass
class DocumentoRelevante:
    """
    Representa um documento relevante encontrado pela busca RAG.

    Attributes:
        titulo (str): Título da nota/documento.
        conteudo (str): Conteúdo completo do documento.
        score_similaridade (float): Score de similaridade com o prompt.
        trecho_relevante (str): Parte mais relevante do conteúdo.
    """
    titulo: str
    conteudo: str
    score_similaridade: float
    trecho_relevante: str

# ==============================================================================
# Classe Principal - Assistente IA Avançado
# ==============================================================================

class AssistenteIAAvancado:
    """
    Assistente IA com suporte a RAG e integração com Ollama e FAISS.
    """

    def __init__(self, modelo_embeddings: str = None):
        """
        Inicializa o assistente IA com configurações do configurador.

        Args:
            modelo_embeddings (str): Nome do modelo de embeddings a utilizar (opcional).
        """
        ollama_config = configurador.obter("modelo_ia", {}) or {}
        embeddings_config = configurador.obter("embeddings", {}) or {}
        rag_config = configurador.obter("rag", {}) or {}

        self.url_ollama = ollama_config.get("url", "http://localhost:11434")
        self.modelo_ia = ollama_config.get("nome", "tinyllama")
        self.max_tokens = ollama_config.get("max_tokens", 1024)
        self.temperatura = ollama_config.get("temperatura", 0.7)
        self.timeout = ollama_config.get("timeout", 30)

        self.modelo_embeddings = None
        self.modelo_embeddings_nome = (
            modelo_embeddings or embeddings_config.get("modelo", "all-MiniLM-L6-v2")
        )
        self.dimensao_embeddings = embeddings_config.get("dimensoes", 384)

        self.max_documentos_contexto = rag_config.get("max_documentos", 3)
        self.limiar_relevancia = rag_config.get("limiar_relevancia", 0.35)
        self.max_caracteres_contexto = rag_config.get("max_caracteres", 2000)

    def inicializar_modelo_embeddings(self) -> bool:
        """
        Inicializa o modelo de embeddings se disponível.

        Returns:
            bool: True se inicializado com sucesso, False caso contrário.
        """
        if not DEPENDENCIAS_AVANCADAS:
            logger.warning("Dependências para embeddings não disponíveis.")
            return False

        try:
            if self.modelo_embeddings is None:
                logger.info(f"Carregando modelo de embeddings: {self.modelo_embeddings_nome}")
                self.modelo_embeddings = SentenceTransformer(self.modelo_embeddings_nome)
                logger.info("Modelo de embeddings carregado com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo de embeddings: {e}")
            return False

    def configurar_ollama(self, url: str, modelo: str, max_tokens: int = 2048,
                          temperatura: float = 0.7, timeout: int = 30):
        """
        Define parâmetros da API Ollama para geração de respostas.

        Args:
            url (str): URL da API Ollama.
            modelo (str): Nome do modelo de linguagem.
            max_tokens (int): Máximo de tokens por resposta.
            temperatura (float): Temperatura da geração.
            timeout (int): Timeout em segundos.
        """
        self.url_ollama = url
        self.modelo_ia = modelo
        self.max_tokens = max_tokens
        self.temperatura = temperatura
        self.timeout = timeout
        logger.info(f"Ollama configurado com sucesso: {url} ({modelo})")


    def recarregar_configuracoes(self):
        """
        Recarrega configurações atualizadas a partir do configurador global.
        """
        ollama_config = configurador.obter_config_ollama()
        embeddings_config = configurador.obter("embeddings", {})
        rag_config = configurador.obter("rag", {})

        self.url_ollama = ollama_config.get("url", self.url_ollama)
        self.modelo_ia = ollama_config.get("modelo", self.modelo_ia)
        self.max_tokens = ollama_config.get("max_tokens", self.max_tokens)
        self.temperatura = ollama_config.get("temperatura", self.temperatura)
        self.timeout = ollama_config.get("timeout", self.timeout)

        self.max_documentos_contexto = rag_config.get("max_documentos_contexto", self.max_documentos_contexto)
        self.limiar_relevancia = rag_config.get("limiar_relevancia", self.limiar_relevancia)
        self.max_caracteres_contexto = rag_config.get("max_caracteres_contexto", self.max_caracteres_contexto)

        logger.info("Configurações recarregadas com sucesso.")

    
    def testar_conexao_ollama(self) -> bool:
        """
        Testa a conexão com o servidor Ollama.

        Returns:
            bool: True se a conexão for bem-sucedida, False caso contrário.
        """
        try:
            response = requests.get(f"{self.url_ollama}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Falha ao conectar com Ollama: {e}")
            return False


    def criar_indice_conteudo(self, notas: List[Dict]) -> bool:
        """
        Cria índice FAISS com embeddings gerados a partir do conteúdo das notas.

        Args:
            notas (List[Dict]): Lista de notas a indexar.

        Returns:
            bool: True se o índice for criado com sucesso, False caso contrário.
        """
        if not DEPENDENCIAS_AVANCADAS or not self.inicializar_modelo_embeddings():
            logger.warning("Não é possível criar índice sem dependências avançadas.")
            return False

        try:
            logger.info(f"Criando índice para {len(notas)} notas...")
            textos = [f"{n.get('titulo', '')}\n{n.get('conteudo', '')}" for n in notas]
            embeddings = self.modelo_embeddings.encode(textos)

            self.indice_conteudo = faiss.IndexFlatL2(embeddings.shape[1])
            self.indice_conteudo.add(embeddings.astype('float32'))

            self.notas_indexadas = notas
            self.mapeamento_indices = {i: nota for i, nota in enumerate(notas)}

            logger.info(f"Índice criado com {len(notas)} documentos.")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar índice: {e}")
            return False


    # ==============================================================================  
    # Busca de Documentos Relevantes
    # ==============================================================================

    def buscar_documentos_relevantes(self, pergunta: str, k: int = 5) -> List[DocumentoRelevante]:
        """
        Busca documentos mais semelhantes à pergunta com base em embeddings.

        Args:
            pergunta (str): Pergunta do utilizador.
            k (int): Quantidade de documentos a retornar.

        Returns:
            List[DocumentoRelevante]: Lista de documentos ordenados por relevância.
        """
        if not DEPENDENCIAS_AVANCADAS or self.indice_conteudo is None:
            logger.warning("Índice não disponível para busca.")
            return []

        try:
            embedding_pergunta = self.modelo_embeddings.encode([pergunta])
            scores, indices = self.indice_conteudo.search(embedding_pergunta.astype('float32'), k)

            documentos = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and score < self.limiar_relevancia:
                    nota = self.mapeamento_indices[idx]
                    documentos.append(DocumentoRelevante(
                        titulo=nota.get('titulo', ''),
                        conteudo=nota.get('conteudo', ''),
                        score_similaridade=float(score),
                        trecho_relevante=nota.get('conteudo', '')[:200] + "..."
                    ))

            return documentos
        except Exception as e:
            logger.error(f"Erro na busca de documentos: {e}")
            return []


    # ==============================================================================  
    # Geração de Respostas (com ou sem IA)
    # ==============================================================================

    def gerar_resposta_com_rag(self, pergunta: str, contexto_adicional: str = "") -> Dict[str, any]:
        """
        Gera uma resposta com base na pergunta, utilizando RAG se possível.

        Args:
            pergunta (str): Pergunta do utilizador.
            contexto_adicional (str): Contexto manual adicional (opcional).

        Returns:
            Dict: Resposta gerada e metadados do processo.
        """
        try:
            ativar_ollama = configurador.obter("modelo_ia", "ativar_ollama", True)
            if not ativar_ollama:
                return {
                    'resposta': "IA Ollama foi desativada pelo utilizador.",
                    'documentos_usados': [],
                    'metodo': 'desativado',
                    'contexto_usado': False
                }

            documentos = self.buscar_documentos_relevantes(pergunta)
            contexto = contexto_adicional

            if documentos:
                contexto += "\n\nDocumentos relevantes:\n"
                for doc in documentos:
                    contexto += f"- {doc.titulo}: {doc.trecho_relevante}\n"

            if self.testar_conexao_ollama():
                resposta = self._gerar_resposta_ollama(pergunta, contexto)
                metodo = 'ollama_rag'
            else:
                resposta = self._gerar_resposta_basica(pergunta, documentos)
                metodo = 'basico'

            return {
                'resposta': resposta,
                'documentos_usados': [doc.titulo for doc in documentos],
                'metodo': metodo,
                'contexto_usado': bool(contexto.strip())
            }

        except Exception as e:
            logger.error(f"Erro ao gerar resposta RAG: {e}")
            return {
                'resposta': f"Erro ao processar pergunta: {e}",
                'documentos_usados': [],
                'metodo': 'erro',
                'contexto_usado': False
            }

    def _gerar_resposta_ollama(self, pergunta: str, contexto: str) -> str:
        """
        Gera resposta através da API do Ollama, usando contexto gerado via RAG.

        Args:
            pergunta (str): Pergunta do utilizador.
            contexto (str): Contexto relevante baseado nas notas.

        Returns:
            str: Resposta textual gerada pelo modelo Ollama.
        """
        try:
            prompt = f"""Idioma da resposta: português de Portugal.

            Contexto: {contexto}

            Pergunta: {pergunta}
            Responda com base no contexto fornecido. A resposta deve ser clara, objetiva e escrita exclusivamente em português de Portugal. 
            Se não encontrar a resposta no contexto, diga isso ao utilizador."""

            payload = {
                "model": self.modelo_ia,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": self.max_tokens,
                    "temperature": self.temperatura
                }
            }

            response = requests.post(
                f"{self.url_ollama}/api/generate",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json().get('response', 'Erro na resposta do Ollama')
            return f"Erro HTTP {response.status_code} do Ollama"

        except Exception as e:
            logger.error(f"Erro ao usar Ollama: {e}")
            return f"Erro ao conectar com Ollama: {e}"

    def _gerar_resposta_basica(self, pergunta: str, documentos: List[DocumentoRelevante]) -> str:
        """
        Gera uma resposta básica listando documentos relevantes, sem IA.

        Args:
            pergunta (str): Pergunta do utilizador.
            documentos (List[DocumentoRelevante]): Documentos relevantes.

        Returns:
            str: Resposta textual.
        """
        if not documentos:
            return f"Não encontrei informações relevantes nas suas notas para responder à pergunta: '{pergunta}'."

        resposta = f"Com base nas suas notas, encontrei {len(documentos)} documento(s) relevante(s):\n\n"
        for i, doc in enumerate(documentos, 1):
            resposta += f"{i}. **{doc.titulo}**\n"
            resposta += f"   {doc.trecho_relevante}\n\n"

        resposta += "Para respostas mais completas, ative o Ollama nas configurações."
        return resposta


# ==============================================================================
# Instância Global
# ==============================================================================

assistente_ia = AssistenteIAAvancado()