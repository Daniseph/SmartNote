"""Módulo com funções de suporte para SmartNote."""
import json
import unicodedata

def remover_acentos(texto):
    """Remove os acentos de um texto, retornando o texto sem caracteres acentuados."""
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

def carregar_palavras_ignoradas():
    """Carrega stopwords de um arquivo JSON.

    Tenta abrir o arquivo 'stopwords.json' e ler a lista de stopwords. 
    Caso o arquivo não exista ou ocorra algum erro, retorna um conjunto padrão de stopwords.
    """
    try:
        with open('stopwords.json', 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except Exception:
        return {'o', 'a', 'de', 'da', 'do', 'para', 'como'}

def salvar_palavras_ignoradas(stopwords):
    """Salva o conjunto de stopwords atual em um arquivo JSON.

    Escreve as stopwords no arquivo 'stopwords.json' em formato JSON, preservando caracteres UTF-8.
    """
    with open('stopwords.json', 'w', encoding='utf-8') as f:
        json.dump(list(stopwords), f, ensure_ascii=False, indent=4)
