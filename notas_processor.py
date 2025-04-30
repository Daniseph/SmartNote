"""Módulo de processamento de notas"""
import os
import re

import faiss

def extrair_conceitos_relevantes(nlp, text, stopwords):
    """Extrai conceitos-chave de um texto utilizando PLN

    Analisa o texto com um pipeline de linguagem natural (spaCy) e retorna uma lista de conceitos
    relevantes (substantivos e nomes próprios) em minúsculas, filtrando palavras curtas e stopwords.
    """
    try:
        if not text or not isinstance(text, str):
            return []
        doc = nlp(text)
        concepts = set()
        for token in doc:
            if token.pos_ in ('NOUN', 'PROPN') and len(token.text.strip()) > 3:
                clean_concept = re.sub(r'[^\w\s-]', '', token.text).lower().strip()
                if clean_concept and clean_concept not in stopwords:
                    concepts.add(clean_concept)
        return list(concepts)
    except Exception as e:
        print(f"Erro na extração de conceitos: {str(e)}")
        return []

def verificar_conexoes_relevantes(conceito, conteudo):
    """Verifica se um conceito aparece de forma relevante dentro do conteúdo fornecido.

    Retorna True se o conceito estiver presente no conteúdo do texto. 

    Função ainda por desenvover (21 de abril a 11 de maio de 2025)
    """
    if conceito in conteudo:
        return True
    return False

def gerar_conexoes_automaticas(notas, nlp, stopwords):
    """Processa a lista de notas, adicionando links wiki [[...]] para conceitos comuns entre notas.

    Retorna a lista de notas com seus conteúdos atualizados com os links adicionados.
    O processamento envolve:
    - Extração de conceitos-chave de cada nota (ignorando stopwords).
    - Identificação de conceitos compartilhados entre notas diferentes.
    - Inserção de links no conteúdo das notas onde esses conceitos aparecem.
    """
    conceitos_por_nota = {}
    for nota in notas:
        conceitos_por_nota[nota['titulo']] = extrair_conceitos_relevantes(nlp, nota['conteudo'], stopwords)
    links_adicionados = set()
    for idx, nota in enumerate(notas):
        conteudo = nota['conteudo']
        print(f"\nProcessando nota: {nota['titulo']} ({idx + 1}/{len(notas)})")
        conceitos_nota_atual = conceitos_por_nota[nota['titulo']]
        print(f"Conceitos identificados na nota '{nota['titulo']}': {conceitos_nota_atual}")
        for conceito in conceitos_nota_atual:
            print(f"\nAnalisando conceito: '{conceito}'")
            if conceito in ['problemas']:
                print(f"⚠️ Ignorando o conceito genérico '{conceito}'.")
                continue
            for other_title, other_concepts in conceitos_por_nota.items():
                if other_title != nota['titulo'] and conceito in other_concepts:
                    if verificar_conexoes_relevantes(conceito, conteudo):
                        link_markup = f'[[{conceito}]]'
                        print(f"🔗 Link sugerido para '{conceito}' em '{nota['titulo']}' -> {link_markup}")
                        if re.search(rf'\b{re.escape(conceito)}\b', conteudo):
                            conteudo = re.sub(rf'\b{re.escape(conceito)}\b', link_markup, conteudo)
                            links_adicionados.add(conceito)
        nota['conteudo'] = conteudo
        status = '✔️' if links_adicionados else '❌'
        print(f"\n{status} Processamento concluído para {nota['titulo']}")
        print(f"Links adicionados até agora: {len(links_adicionados)}")
    print("\n" + "="*50)
    print("PROCESSAMENTO COMPLETO")
    print("="*50)
    return notas

def criar_indice_embeddings(model, titulos):
    """Cria um índice de similaridade para títulos das notas usando embeddings.

    Retorna uma tupla (index, embeddings) onde index é um índice FAISS treinado e embeddings é a matriz de embeddings dos títulos.
    """
    if not titulos:
        return None, None
    embeddings = model.encode(titulos)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings.astype('float32'))
    print(f"Índice FAISS criado com {len(titulos)} embeddings de títulos.")
    return index, embeddings

def encontrar_titulo_semelhante(model, index, arquivos, frase, threshold):
    """Encontra o título de nota mais semelhante a uma frase fornecida usando o índice de embeddings.

    Retorna o título da nota com similaridade acima do limiar especificado, ou None se não encontrar correspondência.
    """
    if index is None or not arquivos:
        print("⚠️ Índice de títulos não inicializado ou lista de notas vazia.")
        return None
    frase_limpa = re.sub(r'\n+', ' ', frase).strip().lower()
    if not frase_limpa:
        return None
    try:
        frase_embed = model.encode([frase_limpa])
        D, I = index.search(frase_embed.astype('float32'), 5)
        for i in range(len(I[0])):
            distancia = D[0][i]
            titulo_encontrado = arquivos[I[0][i]]['titulo']
            print(f"Distância para '{titulo_encontrado}': {distancia}")
            if distancia < threshold:
                return titulo_encontrado
    except Exception as e:
        print(f"Erro na busca por título semelhante '{frase}': {str(e)}")
    return None

def carregar_notas_de_diretorio(diretorio):
    """Carrega todos os arquivos .md de um diretório de notas e retorna uma lista de notas.

    Para cada arquivo Markdown encontrado, extrai o título (linha inicial começando com '#') e o conteúdo completo.
    Retorna uma lista de dicionários, cada um contendo 'titulo', 'conteudo' e 'caminho' da nota.
    """
    notas = []
    for nome_arquivo in os.listdir(diretorio):
        if nome_arquivo.endswith(".md"):
            caminho = os.path.join(diretorio, nome_arquivo)
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
            except Exception as e:
                print(f"Erro ao ler arquivo {nome_arquivo}: {e}")
                continue
            match = re.search(r'^#\s+(.+)$', conteudo, flags=re.MULTILINE)
            titulo = match.group(1).strip() if match else nome_arquivo[:-3]
            notas.append({'titulo': titulo, 'conteudo': conteudo, 'caminho': caminho})
    return notas
