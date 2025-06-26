#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: configuracao.py
Descrição: Sistema de configuração persistente
===============================================================================
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List

STOPWORDS_PATH = "config/stopwords.json"  # Caminho fixo para ficheiro de stopwords personalizadas
logger = logging.getLogger(__name__)


class ConfiguradorSmartNote:
    """
    Gerencia configurações persistentes do SmartNote a partir de ficheiro JSON.

    Permite acessar, modificar e persistir configurações da aplicação de forma estruturada.
    """

    def __init__(self, config_path: str = "config/configuracao.json"):
        """
        Inicializa o gerenciador de configurações com o caminho do ficheiro.

        Args:
            config_path (str): Caminho para o ficheiro de configuração JSON.
        """
        self.config_path = config_path
        self.config_dir = os.path.dirname(config_path)
        self._configuracoes = self._carregar_configuracoes_padrao()
        self._criar_diretorio_config()
        self.carregar_configuracoes()

    # --------------------------------------------------------------------------
    # Inicialização do diretório
    # --------------------------------------------------------------------------
    def _criar_diretorio_config(self):
        """
        Cria o diretório onde as configurações serão salvas, se não existir.
        """
        if self.config_dir and not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    # --------------------------------------------------------------------------
    # Funções específicas para o modelo Ollama
    # --------------------------------------------------------------------------
    def definir_ollama_ativado(self, ativado: bool) -> bool:
        """
        Ativa ou desativa explicitamente o uso do modelo Ollama.

        Args:
            ativado (bool): True para ativar, False para desativar.

        Returns:
            bool: True se operação for bem-sucedida.
        """
        return self.definir("modelo_ia", "ativar_ollama", ativado)


    def ollama_esta_ativado(self) -> bool:
        """
        Verifica se o uso do Ollama está ativado nas configurações.

        Returns:
            bool: True se ativado, False se não ou indefinido.
        """
        return self.obter("modelo_ia", "ativar_ollama", True)

    # ==============================================================================
    # Função: Carregar Configurações Padrão
    # ==============================================================================

    def _carregar_configuracoes_padrao(self) -> Dict[str, Any]:
        """
        Retorna um dicionário com todas as configurações padrão do SmartNote.

        As configurações abrangem desde parâmetros do modelo de IA até aspectos
        de interface, desempenho e privacidade.

        Returns:
            Dict[str, Any]: Estrutura com valores padrão organizados por categoria.
        """
        return {
            # ----------------------------------------------------------------------
            # Configurações do modelo de IA
            # ----------------------------------------------------------------------
            "modelo_ia": {
                "nome": "tinyllama",                     
                "url_ollama": "http://localhost:11434", 
                "timeout": 30,
                "temperatura": 0.7,
                "max_tokens": 1024,                    
                "ativar_ollama": True
            },

            # ----------------------------------------------------------------------
            # Embeddings para similaridade semântica
            # ----------------------------------------------------------------------
            "embeddings": {
                "modelo": "all-MiniLM-L6-v2",             
                "dimensoes": 384,
                "cache_embeddings": True                  
            },

            # ----------------------------------------------------------------------
            # Geração de links automáticos
            # ----------------------------------------------------------------------
            "links": {
                "limiar_similaridade": 0.50,
                "max_links_por_paragrafo": 3,
                "aplicar_apenas_primeira_ocorrencia": True,
                "modo_semantico_ativo": True,
                "confirmar_antes_aplicar": True
            },

            # ----------------------------------------------------------------------
            # Configurações de busca
            # ----------------------------------------------------------------------
            "busca": {
                "destaque_cor": "#FFFF00",            
                "ignorar_acentos": True,
                "busca_semantica_ativa": True,
                "max_resultados": 50
            },

            # ----------------------------------------------------------------------
            # Personalização da interface
            # ----------------------------------------------------------------------
            "interface": {
                "tema": "claro",
                "fonte_tamanho": 12,
                "fonte_familia": "Arial",
                "texto_negrito": False,              
                "texto_italico": False,                  
                "mostrar_backlinks": True,
                "auto_salvar": True,
                "intervalo_auto_salvar": 300            
            },

            # ----------------------------------------------------------------------
            # Desempenho e limites
            # ----------------------------------------------------------------------
            "performance": {
                "max_notas_cache": 500,                    
                "max_embeddings_cache": 2000,
                "reindexar_automaticamente": False,
                "threads_processamento": 1
            },

            # ----------------------------------------------------------------------
            # Privacidade e anonimato
            # ----------------------------------------------------------------------
            "privacidade": {
                "modo_offline": True,
                "salvar_historico_pesquisa": False,
                "logs_detalhados": False
            },

            # ----------------------------------------------------------------------
            # RAG (Retrieval-Augmented Generation)
            # ----------------------------------------------------------------------
            "rag": {
                "max_documentos_contexto": 3,
                "limiar_relevancia": 0.35,
                "max_caracteres_contexto": 2000
            }
        }


    def carregar_configuracoes(self) -> bool:
        """
        Carrega as configurações a partir do ficheiro JSON e aplica validação.

        Returns:
            bool: True se o carregamento foi bem-sucedido, False caso contrário.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_ficheiro = json.load(f)

                    erros = self.validar_configuracoes(config_ficheiro)
                    if erros:
                        logger.warning(f"Configurações inválidas: {erros}")
                        config_ficheiro = self._corrigir_configuracoes(config_ficheiro)

                    self._merge_configuracoes(config_ficheiro)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            self._configuracoes = self._carregar_configuracoes_padrao()
            return False


    def _corrigir_configuracoes(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Corrige valores inválidos em configurações numéricas com base em limites seguros.

        Args:
            config (Dict[str, Any]): Configurações carregadas do ficheiro.

        Returns:
            Dict[str, Any]: Configurações corrigidas.
        """
        for secao, chaves in [
            ("links", ["limiar_similaridade"]),
            ("performance", ["max_notas_cache", "max_embeddings_cache"]),
            ("rag", ["limiar_relevancia"])
        ]:
            if secao in config:
                for chave in chaves:
                    if chave in config[secao]:
                        try:
                            valor = float(config[secao][chave])
                            if "similaridade" in chave or "relevancia" in chave:
                                if not 0.0 <= valor <= 1.0:
                                    config[secao][chave] = 0.5
                            elif "cache" in chave:
                                if valor < 10:
                                    config[secao][chave] = 100
                        except (TypeError, ValueError):
                            config[secao].pop(chave, None)
        return config


    def _merge_configuracoes(self, config_ficheiro: Dict[str, Any]):
        """
        Mescla as configurações carregadas com as configurações padrão existentes.

        Args:
            config_ficheiro (Dict[str, Any]): Configurações lidas do ficheiro.
        """
        for secao, valores in config_ficheiro.items():
            if secao in self._configuracoes and isinstance(valores, dict):
                for chave, valor in valores.items():
                    if chave in self._configuracoes[secao]:
                        self._configuracoes[secao][chave] = valor
                    else:
                        logger.warning(f"Chave desconhecida: {secao}.{chave}")
            else:
                logger.warning(f"Seção desconhecida: {secao}")
                if secao == "rag":
                    self._configuracoes[secao] = valores


    def salvar_configuracoes(self) -> bool:
        """
        Salva as configurações atuais no ficheiro JSON.

        Returns:
            bool: True se o salvamento for bem-sucedido, False caso contrário.
        """
        try:
            self._criar_diretorio_config()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._configuracoes, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            return False


    def obter(self, secao: str, chave: str = None, padrao: Any = None) -> Any:
        """
        Obtém um valor de configuração de uma seção, com fallback seguro.

        Args:
            secao (str): Nome da seção.
            chave (str, optional): Nome da chave dentro da seção. Se None, retorna a seção completa.
            padrao (Any): Valor a retornar em caso de erro ou ausência.

        Returns:
            Any: Valor encontrado ou valor padrão.
        """
        try:
            secao_data = self._configuracoes.get(secao, {})
            if not isinstance(secao_data, dict):
                secao_data = {}
                self._configuracoes[secao] = secao_data

            if chave is None:
                return secao_data

            valor = secao_data.get(chave)
            return padrao if valor is None else valor

        except Exception:
            return padrao if chave is None else {}


    def definir(self, secao: str, chave: str, valor: Any) -> bool:
        """
        Define ou atualiza um valor de configuração.

        Args:
            secao (str): Nome da seção.
            chave (str): Nome da chave dentro da seção.
            valor (Any): Valor a ser atribuído.

        Returns:
            bool: True se definido com sucesso, False em caso de erro ou chave inválida.
        """
        try:
            if secao not in self._configuracoes:
                if secao not in self._carregar_configuracoes_padrao():
                    logger.warning(f"Tentativa de criar seção desconhecida: {secao}")
                    return False
                self._configuracoes[secao] = {}

            self._configuracoes[secao][chave] = valor
            return True
        except Exception as e:
            logger.error(f"Erro ao definir configuração: {e}")
            return False


    def obter_modelo_ia(self) -> Dict[str, Any]:
        """
        Retorna as configurações do modelo de IA.

        Returns:
            Dict[str, Any]: Configurações da seção 'modelo_ia'.
        """
        return self.obter("modelo_ia", padrao={})


    def obter_config_links(self) -> Dict[str, Any]:
        """
        Retorna as configurações relacionadas a geração de links.

        Returns:
            Dict[str, Any]: Configurações da seção 'links'.
        """
        return self.obter("links", padrao={})


    def obter_config_rag(self) -> Dict[str, Any]:
        """
        Retorna as configurações da funcionalidade RAG.

        Returns:
            Dict[str, Any]: Configurações da seção 'rag'.
        """
        return self.obter("rag", padrao={})


    def obter_config_busca(self) -> Dict[str, Any]:
        """
        Retorna as configurações da ferramenta de busca.

        Returns:
            Dict[str, Any]: Configurações da seção 'busca'.
        """
        return self.obter("busca", padrao={})


    def obter_config_interface(self) -> Dict[str, Any]:
        """
        Retorna as configurações da interface do utilizador.

        Returns:
            Dict[str, Any]: Configurações da seção 'interface'.
        """
        return self.obter("interface", padrao={})

    
    def validar_configuracoes(self, config: Optional[Dict] = None) -> Dict[str, str]:
        """
        Valida os valores das configurações fornecidas.

        Args:
            config (Optional[Dict]): Estrutura de configurações a validar.
                                    Se None, utiliza as configurações internas.

        Returns:
            Dict[str, str]: Dicionário de erros encontrados, onde a chave indica
                            o caminho da configuração e o valor descreve o erro.
        """
        config = config or self._configuracoes
        erros = {}

        modelo_ia = config.get("modelo_ia", {})
        if not modelo_ia.get("nome"):
            erros["modelo_ia.nome"] = "Nome do modelo não pode estar vazio"
        elif not self.validar_nome_modelo(modelo_ia["nome"]):
            erros["modelo_ia.nome"] = "Nome de modelo inválido"

        url_ollama = modelo_ia.get("url_ollama", "")
        if url_ollama and not self.validar_url_ollama(url_ollama):
            erros["modelo_ia.url_ollama"] = "URL do Ollama inválida"

        limiar = config.get("links", {}).get("limiar_similaridade", 0.50)
        if not 0.0 <= limiar <= 1.0:
            erros["links.limiar_similaridade"] = "Limiar deve estar entre 0.0 e 1.0"

        max_notas = config.get("performance", {}).get("max_notas_cache", 1000)
        if max_notas < 10:
            erros["performance.max_notas_cache"] = "Mínimo de 10 notas em cache"

        limiar_rag = config.get("rag", {}).get("limiar_relevancia", 0.3)
        if not 0.0 <= limiar_rag <= 1.0:
            erros["rag.limiar_relevancia"] = "Limiar de relevância deve estar entre 0.0 e 1.0"

        return erros

    @staticmethod
    def validar_url_ollama(url: str) -> bool:
        """
        Verifica se a URL do Ollama tem um formato válido.

        Args:
            url (str): URL a validar.

        Returns:
            bool: True se começar por 'http://' ou 'https://'.
        """
        return url.startswith("http://") or url.startswith("https://")

    @staticmethod
    def validar_nome_modelo(modelo: str) -> bool:
        """
        Verifica se o nome do modelo é válido.

        Args:
            modelo (str): Nome a validar.

        Returns:
            bool: True se o nome tem pelo menos 3 caracteres e não contém '/'.
        """
        return bool(modelo) and len(modelo) >= 3 and '/' not in modelo


    def obter_config_ollama(self) -> Dict[str, Any]:
        """
        Retorna as configurações específicas do modelo Ollama.

        Returns:
            Dict[str, Any]: Dicionário com os parâmetros usados para chamadas ao modelo.
        """
        return {
            "url": self.obter("modelo_ia", "url_ollama", "http://localhost:11434"),
            "modelo": self.obter("modelo_ia", "nome", "tinyllama"),
            "temperatura": self.obter("modelo_ia", "temperatura", 0.7),
            "timeout": self.obter("modelo_ia", "timeout", 30),
            "max_tokens": self.obter("modelo_ia", "max_tokens", 1024),
            "ativado": self.obter("modelo_ia", "ativar_ollama", True)
        }


    def resetar_para_padrao(self):
        """
        Restaura todas as configurações para os valores padrão e salva no ficheiro.
        """
        self._configuracoes = self._carregar_configuracoes_padrao()
        self.salvar_configuracoes()


    def exportar_configuracoes(self, caminho: str) -> bool:
        """
        Exporta as configurações atuais para um ficheiro externo.

        Args:
            caminho (str): Caminho do ficheiro de destino.

        Returns:
            bool: True se exportado com sucesso, False caso contrário.
        """
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(self._configuracoes, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar configurações: {e}")
            return False


    def importar_configuracoes(self, caminho: str) -> bool:
        """
        Importa configurações a partir de um ficheiro externo.

        Args:
            caminho (str): Caminho do ficheiro JSON a importar.

        Returns:
            bool: True se a importação for válida e bem-sucedida, False caso contrário.
        """
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                config_importada = json.load(f)

                erros = self.validar_configuracoes(config_importada)
                if erros:
                    logger.warning(f"Configurações importadas inválidas: {erros}")
                    return False

                self._merge_configuracoes(config_importada)
                self.salvar_configuracoes()
            return True
        except Exception as e:
            logger.error(f"Erro ao importar configurações: {e}")
            return False


    def obter_stopwords_personalizadas(self) -> List[str]:
        """
        Retorna a lista de stopwords personalizadas carregadas do ficheiro.

        Returns:
            List[str]: Lista de termos, ou lista vazia em caso de erro.
        """
        try:
            if os.path.exists(STOPWORDS_PATH):
                with open(STOPWORDS_PATH, 'r', encoding='utf-8') as f:
                    return sorted(set(json.load(f)))
        except Exception as e:
            logger.error(f"Erro ao carregar stopwords: {e}")
        return []


    def salvar_stopwords_personalizadas(self, lista: List[str]) -> bool:
        """
        Salva a lista de stopwords personalizadas no ficheiro correspondente.

        Args:
            lista (List[str]): Lista de termos a salvar.

        Returns:
            bool: True se o salvamento for bem-sucedido, False caso contrário.
        """
        try:
            os.makedirs(os.path.dirname(STOPWORDS_PATH), exist_ok=True)
            with open(STOPWORDS_PATH, 'w', encoding='utf-8') as f:
                json.dump(sorted(set(lista)), f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar stopwords: {e}")
            return False


# ==============================================================================
# Instância Global
# ==============================================================================

configurador = ConfiguradorSmartNote()
