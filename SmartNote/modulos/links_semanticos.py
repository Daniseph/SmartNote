#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: links_semanticos.py
Descrição: Geração de links semânticos entre notas utilizando embeddings e FAISS.
===============================================================================
"""

import logging
import re
import faiss
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from modulos.gerador_links import LinkSugerido
from dataclasses import dataclass
from modulos.conceitos import extrator_conceitos, Conceito
from modulos.similaridade import SimilaridadeUtils
from unidecode import unidecode

logger = logging.getLogger(__name__)


def termo_presente_em(texto: str, termo: str) -> bool:
    """
    Verifica se o termo aparece no texto, ignorando acentos e caixa.

    Args:
        texto (str): Texto no qual procurar o termo.
        termo (str): Termo a procurar.

    Returns:
        bool: True se o termo estiver presente no texto, False caso contrário.
    """
    texto = unidecode(texto.lower())
    termo = unidecode(termo.lower())
    return termo in texto

class GeradorLinksSemanticos:
    """
    Classe responsável por gerar links semânticos entre notas.
    Utiliza embeddings de frases e índice vetorial com FAISS.
    """

    def __init__(self, modelo_embeddings: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Inicializa o gerador de links com modelo de embeddings.

        Args:
            modelo_embeddings (str): Nome ou caminho do modelo da SentenceTransformer.
        """
        self.modelo_embeddings = SentenceTransformer(modelo_embeddings)
        self.indice_titulos: Optional[faiss.Index] = None
        self.titulos_indexados: List[str] = []
        self.cache_links: Dict[str, List[LinkSugerido]] = {}

        # Configurações padrão
        self.limiar_similaridade = 0.05
        self.max_links_por_paragrafo = 3
        self.aplicar_apenas_primeira_ocorrencia = True
        self.modo_semantico_ativo = True

        # Termos genéricos a ignorar
        self.termos_genericos = extrator_conceitos.stopwords_personalizadas


    def configurar_parametros(self, limiar_similaridade: float = 0.05, max_links_por_paragrafo: int = 3,
                              aplicar_apenas_primeira: bool = True, modo_semantico: bool = True):
        """
        Configura os parâmetros de funcionamento do gerador.

        Args:
            limiar_similaridade (float): Score mínimo de similaridade.
            max_links_por_paragrafo (int): Quantidade máxima de links por parágrafo.
            aplicar_apenas_primeira (bool): Se apenas a primeira ocorrência do termo deve ser usada.
            modo_semantico (bool): Ativa ou desativa o modo semântico.
        """
        self.limiar_similaridade = limiar_similaridade
        self.max_links_por_paragrafo = max_links_por_paragrafo
        self.aplicar_apenas_primeira_ocorrencia = aplicar_apenas_primeira
        self.modo_semantico_ativo = modo_semantico

    def criar_indice_titulos(self, notas: List[Dict]) -> bool:
        """
        Cria o índice vetorial FAISS com contexto enriquecido de cada nota.

        Cada entrada do índice representa um vetor que combina:
        - Título da nota
        - Palavras-chave extraídas
        - Primeiro trecho do conteúdo

        Args:
            notas (List[Dict]): Lista de dicionários contendo 'titulo' e 'conteudo'.

        Returns:
            bool: True se o índice foi criado com sucesso, False caso contrário.
        """
        try:
            if not notas:
                return False

            if self.modelo_embeddings is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    self.modelo_embeddings = SentenceTransformer("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")
                    logger.info("Modelo de embeddings carregado com sucesso.")
                except Exception as e:
                    logger.error(f"Erro ao carregar modelo de embeddings: {e}")
                    return False

            textos_contexto = []
            self.mapeamento_titulos = {}  # ID numérico para título
            self.ids_indexados = []       # IDs na ordem dos embeddings

            for idx, nota in enumerate(notas):
                titulo = nota.get('titulo', '').strip()
                conteudo = nota.get('conteudo', '').strip()

                if not titulo or len(titulo) < 3:
                    continue

                palavras_chave = extrator_conceitos.extrair_conceitos_avancados(conteudo, titulo)

                termos_validos = []
                for c in palavras_chave:
                    if isinstance(c, Conceito):
                        termos_validos.append(c.termo)
                    elif isinstance(c, str):
                        termos_validos.append(c)

                palavras_chave_texto = ', '.join(termos_validos)
                trecho_inicial = conteudo.replace('\n', ' ').strip()[:500]
                texto_contexto = f"{titulo}. {palavras_chave_texto}. {trecho_inicial}"

                textos_contexto.append(texto_contexto)
                self.mapeamento_titulos[idx] = titulo
                self.ids_indexados.append(idx)

            if not textos_contexto:
                return False

            embeddings = self.modelo_embeddings.encode(textos_contexto)
            embeddings = np.asarray(embeddings, dtype='float32')

            dimensao = embeddings.shape[1]
            self.indice_titulos = faiss.IndexFlatL2(dimensao)
            self.indice_titulos.add(embeddings)

            logger.info(f"Índice semântico criado com {len(textos_contexto)} notas.")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar índice de títulos: {e}")
            return False

    def gerar_links_sugeridos(self, notas: List[Dict]) -> Dict[str, List[LinkSugerido]]:
        """
        Gera links sugeridos para todas as notas fornecidas, combinando:
        - Links literais (baseados em matching exato de conceitos).
        - Links semânticos (baseados em similaridade vetorial).

        Args:
            notas (List[Dict]): Lista de notas com 'titulo' e 'conteudo'.

        Returns:
            Dict[str, List[LinkSugerido]]: Dicionário com o título da nota como chave
                                           e lista de links sugeridos como valor.
        """
        links_por_nota = {}

        for nota in notas:
            titulo_nota = nota['titulo']
            links_nota = []

            # 1. Links literais
            links_literais = self._gerar_links_literais(nota, notas)
            links_nota.extend(links_literais)

            # 2. Links semânticos (se ativo)
            links_semanticos = []
            if self.modo_semantico_ativo and self.indice_titulos:
                links_semanticos = self._gerar_links_semanticos(nota, notas)
                links_nota.extend(links_semanticos)

            # 3. Filtragem e priorização
            links_filtrados = self._filtrar_links(links_nota, nota['conteudo'])
            links_por_nota[titulo_nota] = links_filtrados

            logger.debug(f"[{titulo_nota}] Links literais gerados: {len(links_literais)}")
            logger.debug(f"[{titulo_nota}] Links semânticos gerados: {len(links_semanticos)}")

        return links_por_nota

    def _gerar_links_literais(self, nota: Dict, todas_notas: List[Dict]) -> List[LinkSugerido]:
        """
        Gera links literais para uma nota, com base na presença exata de termos/conceitos.

        Args:
            nota (Dict): Nota de origem para a qual os links serão gerados.
            todas_notas (List[Dict]): Lista de todas as notas do sistema.

        Returns:
            List[LinkSugerido]: Lista de links sugeridos do tipo literal.
        """
        links = []
        conteudo = nota['conteudo']
        titulo_atual = nota['titulo']

        conceitos_nota = extrator_conceitos.extrair_conceitos_avancados(conteudo, titulo_atual)

        for conceito in conceitos_nota:
            termo = conceito.termo

            if termo.lower() in self.termos_genericos:
                continue

            posicoes = self._encontrar_posicoes_termo(termo, conteudo)
            if not posicoes:
                continue

            for outra_nota in todas_notas:
                if outra_nota['titulo'] == titulo_atual:
                    continue

                if self._termo_relevante_em_nota(termo, outra_nota):
                    for pos in posicoes:
                        contexto = self._extrair_contexto(conteudo, pos, termo)
                        links.append(LinkSugerido(
                            termo=termo,
                            nota_destino=outra_nota['titulo'],
                            tipo='literal',
                            contexto=contexto,
                            score_similaridade=0.9,
                            posicao_inicio=pos,
                            posicao_fim=pos + len(termo)
                        ))

        return links


    def _encontrar_mais_proximo(self, termo: str, candidatos: List[str]) -> Tuple[str, float]:
        """
        Encontra o candidato semanticamente mais próximo ao termo dado.
        Retorna uma tupla (termo_mais_proximo, score).
        """
        if not candidatos or not self.modelo_embeddings:
            return "", 0.0

        try:
            emb_termo = self.modelo_embeddings.encode([termo])[0]
            emb_candidatos = self.modelo_embeddings.encode(candidatos)

            scores = [SimilaridadeUtils.similaridade(emb_termo, emb) for emb in emb_candidatos]
            idx_max = int(np.argmax(scores))

            return candidatos[idx_max], float(scores[idx_max])
        
        except Exception as e:
            logger.warning(f"Erro ao encontrar termo mais próximo: {e}")
            return "", 0.0

    def _encontrar_mais_proximo(self, termo: str, candidatos: List[str]) -> Tuple[str, float]:
        """
        Encontra o candidato semanticamente mais próximo ao termo fornecido.

        Args:
            termo (str): Termo de origem.
            candidatos (List[str]): Lista de termos candidatos.

        Returns:
            Tuple[str, float]: Tupla com o termo mais próximo e o respetivo score de similaridade.
        """
        try:
            emb_termo = self.modelo_embeddings.encode([termo])[0]
            emb_candidatos = self.modelo_embeddings.encode(candidatos)

            scores = [SimilaridadeUtils.similaridade(emb_termo, emb) for emb in emb_candidatos]
            idx_max = int(np.argmax(scores))

            return candidatos[idx_max], float(scores[idx_max])

        except Exception as e:
            logger.warning(f"Erro ao encontrar termo mais próximo: {e}")
            return "", 0.0

    def _encontrar_termos_semanticos_unilaterais(self, origem: List[str], destino: List[str]) -> List[str]:
        """
        Retorna termos de 'origem' que são semanticamente similares a qualquer termo em 'destino',
        mesmo que não haja correspondência literal.

        Args:
            origem (List[str]): Lista de termos origem.
            destino (List[str]): Lista de termos destino.

        Returns:
            List[str]: Lista de termos de 'origem' considerados semanticamente próximos.
        """
        resultados = []
        try:
            emb_origem = self.modelo_embeddings.encode(origem)
            emb_destino = self.modelo_embeddings.encode(destino)

            for i, vetor_o in enumerate(emb_origem):
                termo_o = origem[i]
                for j, vetor_d in enumerate(emb_destino):
                    termo_d = destino[j]
                    score = SimilaridadeUtils.similaridade(vetor_o, vetor_d)
                    if score >= self.limiar_similaridade:
                        resultados.append(termo_o)
                        break  # Evita repetições excessivas

            return list(set(resultados))

        except Exception as e:
            logger.warning(f"Erro ao calcular similaridade unilateral: {e}")
            return []
                                      
    def _extrair_ngrams(self, texto: str, max_n: int = 3) -> List[str]:
        """
        Extrai n-gramas (1 a n palavras) de um texto, ignorando palavras muito curtas.

        Args:
            texto (str): Texto de entrada.
            max_n (int): Máximo tamanho de n-gramas (padrão: 3).

        Returns:
            List[str]: Lista de n-gramas gerados.
        """
        tokens = [t for t in re.findall(r'\b\w+\b', texto.lower()) if len(t) > 2]
        ngrams = []
        for n in range(1, max_n + 1):
            ngrams += [' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
        return ngrams

    def _gerar_links_semanticos(self, nota: Dict, todas_notas: List[Dict]) -> List[LinkSugerido]:
        """
        Gera links entre parágrafos da nota e outras notas com base em similaridade semântica.

        Args:
            nota (Dict): Nota atual em análise.
            todas_notas (List[Dict]): Lista completa de notas.

        Returns:
            List[LinkSugerido]: Lista de links sugeridos do tipo semântico.
        """
        links = []

        if not self.indice_titulos or not self.modelo_embeddings:
            return links

        conteudo = nota['conteudo']
        titulo_atual = nota['titulo']
        paragrafos = [p.strip() for p in conteudo.split('\n\n') if p.strip()]

        for paragrafo in paragrafos:
            if len(paragrafo.split()) < 3:
                continue

            titulos_similares = self._buscar_titulos_similares(paragrafo)

            for titulo_similar, score in titulos_similares:
                if titulo_similar == titulo_atual:
                    continue

                nota_similar = self._encontrar_nota_por_titulo(titulo_similar, todas_notas)
                if not nota_similar:
                    continue

                conceitos_paragrafo = extrator_conceitos.extrair_conceitos_avancados(paragrafo, titulo_atual)
                conceitos_similar = extrator_conceitos.extrair_conceitos_avancados(
                    nota_similar['conteudo'], nota_similar['titulo']
                )

                termos_paragrafo = [c.termo for c in conceitos_paragrafo if len(c.termo) > 2]
                termos_similar = [c.termo for c in conceitos_similar if len(c.termo) > 2]

                termos_semanticos = self._encontrar_termos_semanticos_unilaterais(termos_similar, termos_paragrafo)

                for termo in termos_semanticos:
                    if not termo or len(termo.strip()) < 3:
                        continue
                    if any(c in termo for c in ['_', '/', '\\']):
                        continue
                    if termo.count(" ") > 3:
                        continue
                    if not termo.replace(" ", "").isalnum():
                        continue

                    if not termo_presente_em(nota['conteudo'], termo) and not termo_presente_em(nota_similar['conteudo'], termo):
                        continue

                    posicoes = self._encontrar_posicoes_termo(termo, conteudo)

                    if posicoes:
                        for posicao in posicoes:
                            contexto = self._extrair_contexto(conteudo, posicao, termo)
                            links.append(LinkSugerido(
                                termo=termo,
                                nota_destino=titulo_similar,
                                posicao_inicio=posicao,
                                posicao_fim=posicao + len(termo),
                                score_similaridade=score,
                                contexto=contexto,
                                tipo="semantico"
                            ))
                    else:
                        candidatos = self._extrair_ngrams(paragrafo)
                        termo_similar, sim_score = self._encontrar_mais_proximo(termo, candidatos)

                        if sim_score >= 0.80:
                            pos_local = paragrafo.lower().find(termo_similar.lower())
                            if pos_local >= 0:
                                posicao = conteudo.find(paragrafo) + pos_local
                                contexto = self._extrair_contexto(conteudo, posicao, termo_similar)
                                links.append(LinkSugerido(
                                    termo=termo,
                                    nota_destino=titulo_similar,
                                    posicao_inicio=posicao,
                                    posicao_fim=posicao + len(termo_similar),
                                    score_similaridade=score,
                                    contexto=contexto,
                                    tipo="semantico"
                                ))
                        else:
                            contexto_virtual = f"(semântico) Conceito relacionado: {termo}"
                            links.append(LinkSugerido(
                                termo=termo,
                                nota_destino=titulo_similar,
                                posicao_inicio=-1,
                                posicao_fim=-1,
                                score_similaridade=score,
                                contexto=contexto_virtual,
                                tipo="semantico"
                            ))

        return links
    
    def _buscar_titulos_similares(self, texto: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Busca títulos similares a um texto usando FAISS."""
        try:
            if not self.indice_titulos or not self.mapeamento_titulos:
                print("⚠️ Índice ou dados de títulos não inicializados.")
                return []

            embedding_texto = self.modelo_embeddings.encode([texto])
            embedding_texto = np.asarray(embedding_texto).astype('float32')

            distancias, indices = self.indice_titulos.search(embedding_texto, top_k)

            resultados = []
            for i in range(top_k):
                try:
                    distancia = float(distancias[0][i])
                    indice_faiss = int(indices[0][i])

                    print(f"🔎 Índice FAISS: {indice_faiss} (tipo={type(indice_faiss)}), Distância: {distancia}")

                    # Verificar se FAISS retornou um índice válido
                    if indice_faiss == -1 or indice_faiss not in self.mapeamento_titulos:
                        print(f"⚠️ Índice FAISS fora de alcance: {indice_faiss}")
                        continue

                    titulo = self.mapeamento_titulos[indice_faiss]
                    score = 1.0 / (1.0 + distancia)

                    status = "✅" if score >= self.limiar_similaridade else "❌"
                    print(f"{status} {titulo} (score={score:.4f}, dist={distancia:.2f})")

                    if score >= self.limiar_similaridade:
                        resultados.append((titulo, score))

                except Exception as e:
                    print(f"❌ Erro ao processar resultado {i}: {e}")
                    continue

            return resultados

        except Exception as e:
            print(f"❌ Erro geral na busca de títulos similares: {e}")
            return []

    def _buscar_titulos_similares(self, texto: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Busca os títulos mais semanticamente similares ao texto fornecido, usando FAISS.

        Args:
            texto (str): Texto de entrada para comparação.
            top_k (int): Número de resultados mais próximos a retornar.

        Returns:
            List[Tuple[str, float]]: Lista de tuplas (título, score de similaridade).
        """
        try:
            if not self.indice_titulos or not self.mapeamento_titulos:
                return []

            embedding_texto = self.modelo_embeddings.encode([texto])
            embedding_texto = np.asarray(embedding_texto).astype('float32')

            distancias, indices = self.indice_titulos.search(embedding_texto, top_k)

            resultados = []
            for i in range(top_k):
                try:
                    distancia = float(distancias[0][i])
                    indice_faiss = int(indices[0][i])

                    if indice_faiss == -1 or indice_faiss not in self.mapeamento_titulos:
                        continue

                    titulo = self.mapeamento_titulos[indice_faiss]
                    score = 1.0 / (1.0 + distancia)

                    if score >= self.limiar_similaridade:
                        resultados.append((titulo, score))

                except Exception as e:
                    continue

            return resultados

        except Exception as e:
            return []

    def _termo_relevante_em_nota(self, termo: str, nota: Dict) -> bool:
        """
        Verifica se o termo é relevante dentro de uma nota (título ou conceitos).

        Args:
            termo (str): Termo a verificar.
            nota (Dict): Nota a ser analisada.

        Returns:
            bool: True se o termo estiver presente como conceito ou no título.
        """
        titulo = nota['titulo'].lower()
        conteudo = nota['conteudo'].lower()
        termo_lower = termo.lower()

        if termo_lower in titulo:
            return True

        conceitos_nota = extrator_conceitos.extrair_conceitos_avancados(nota['conteudo'])
        termos_nota = {c.termo.lower() for c in conceitos_nota}

        return termo_lower in termos_nota

    def _encontrar_posicoes_termo(self, termo: str, conteudo: str) -> List[int]:
        """
        Encontra todas as posições onde o termo aparece no conteúdo.

        Args:
            termo (str): Termo a localizar.
            conteudo (str): Texto completo onde procurar.

        Returns:
            List[int]: Lista de posições iniciais de ocorrência.
        """
        posicoes = []
        padrao = rf'\b{re.escape(termo)}\b'

        for match in re.finditer(padrao, conteudo, re.IGNORECASE):
            posicoes.append(match.start())

        return posicoes

    def _extrair_contexto(self, conteudo: str, posicao: int, termo: str) -> str:
        """
        Extrai um trecho de texto ao redor de uma posição para fornecer contexto.

        Args:
            conteudo (str): Texto completo.
            posicao (int): Posição inicial do termo.
            termo (str): Termo encontrado.

        Returns:
            str: Texto com cerca de 50 caracteres antes e depois do termo.
        """
        inicio = max(0, posicao - 50)
        fim = min(len(conteudo), posicao + len(termo) + 50)
        contexto = conteudo[inicio:fim].strip()

        if inicio > 0:
            contexto = "..." + contexto
        if fim < len(conteudo):
            contexto = contexto + "..."

        return contexto

    def _encontrar_nota_por_titulo(self, titulo: str, notas: List[Dict]) -> Optional[Dict]:
        """Encontra uma nota pelo título."""
        for nota in notas:
            if nota['titulo'] == titulo:
                return nota
        return None
    
    def _encontrar_nota_por_titulo(self, titulo: str, notas: List[Dict]) -> Optional[Dict]:
        """
        Procura uma nota com base no título exato.

        Args:
            titulo (str): Título da nota a encontrar.
            notas (List[Dict]): Lista de todas as notas disponíveis.

        Returns:
            Optional[Dict]: Nota encontrada, ou None se não existir.
        """
        for nota in notas:
            if nota['titulo'] == titulo:
                return nota
        return None

    def _filtrar_links(self, links: List[LinkSugerido], conteudo: str) -> List[LinkSugerido]:
        """
        Filtra e organiza links, limitando por parágrafo e evitando duplicações.

        Args:
            links (List[LinkSugerido]): Lista de links brutos.
            conteudo (str): Conteúdo da nota original.

        Returns:
            List[LinkSugerido]: Lista final filtrada e ordenada de links.
        """
        links_por_paragrafo = {}
        links_sem_posicao = []

        for link in links:
            if link.posicao_inicio < 0:
                links_sem_posicao.append(link)
                continue

            num_paragrafo = self._encontrar_paragrafo(link.posicao_inicio, conteudo)

            if num_paragrafo not in links_por_paragrafo:
                links_por_paragrafo[num_paragrafo] = []

            links_por_paragrafo[num_paragrafo].append(link)

        links_filtrados = []

        for num_paragrafo, links_paragrafo in links_por_paragrafo.items():
            links_paragrafo.sort(key=lambda l: l.score_similaridade, reverse=True)
            links_selecionados = links_paragrafo[:self.max_links_por_paragrafo]

            if self.aplicar_apenas_primeira_ocorrencia:
                termos_vistos = set()
                for link in links_selecionados:
                    chave = (link.termo, link.nota_destino)
                    if chave not in termos_vistos:
                        termos_vistos.add(chave)
                        links_filtrados.append(link)
            else:
                links_filtrados.extend(links_selecionados)

        return links_filtrados + links_sem_posicao

    def _encontrar_paragrafo(self, posicao: int, conteudo: str) -> int:
        """
        Determina o número do parágrafo a partir da posição no texto.

        Args:
            posicao (int): Posição absoluta no conteúdo.
            conteudo (str): Texto completo da nota.

        Returns:
            int: Índice do parágrafo.
        """
        texto_ate_posicao = conteudo[:posicao]
        return texto_ate_posicao.count('\n\n')

    def aplicar_links_em_memoria(self, conteudo: str, sugestoes: List[LinkSugerido]) -> str:
        """
        Aplica os links sugeridos no conteúdo textual de forma segura.

        Args:
            conteudo (str): Texto original da nota.
            sugestoes (List[LinkSugerido]): Lista de sugestões de links.

        Returns:
            str: Conteúdo com links aplicados.
        """
        try:
            conteudo_modificado = conteudo
            usados = set()

            for sugestao in sorted(sugestoes, key=lambda s: s.score_similaridade, reverse=True):
                termo = sugestao.termo
                destino = sugestao.nota_destino
                chave = (termo.lower(), destino.lower())

                if chave in usados:
                    continue

                padrao_linkado = re.compile(rf"\[\[.*?\|{re.escape(termo)}\]\]", re.IGNORECASE)
                if padrao_linkado.search(conteudo_modificado):
                    continue

                padrao = re.compile(rf"\b{re.escape(termo)}\b", re.IGNORECASE)
                match = padrao.search(conteudo_modificado)
                if not match:
                    continue

                termo_encontrado = match.group()
                if sugestao.tipo == "semantico":
                    link = f"[[sem:{destino}|{termo_encontrado}]]"
                else:
                    link = f"[[{destino}|{termo_encontrado}]]"

                conteudo_modificado = (
                    conteudo_modificado[:match.start()] + link + conteudo_modificado[match.end():]
                )

                usados.add(chave)

            return conteudo_modificado

        except Exception as e:
            logger.info(f"Erro ao aplicar links em memória: {e}")
            return conteudo  

    def limpar_cache(self):
        """
        Limpa a cache interna de links sugeridos, se existente.

        Útil para garantir que uma nova execução de geração de links
        não utilize resultados antigos armazenados.
        """
        self.cache_links.clear()

# ==============================================================================
# Instância global do gerador
# ==============================================================================

gerador_links = GeradorLinksSemanticos()