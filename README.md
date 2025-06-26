#SmartNote

SmartNote é uma aplicação de notas que permite importar, editar e explorar ficheiros em Markdown. Oferece funcionalidades avançadas como análise de texto, criação automática de ligações entre notas e integração com uma inteligência artificial local.

#Funcionalidades principais

Importação de notas em formato Markdown com metadados

Extração automática de conceitos e entidades com processamento de linguagem natural (spaCy)

Criação automática de ligações entre notas relacionadas usando embeddings e FAISS

Pesquisa avançada com suporte a expressões regulares, acentos e distinção entre maiúsculas e minúsculas

Assistente com IA local, com respostas baseadas no conteúdo das notas (usando Ollama)

Gestão de backlinks com opção para visualizar e remover

Várias opções de configuração (modo de análise, modelo de IA, palavras ignoradas, etc.)

#Interface

A interface, construída com PyQt5, permite:

Editar notas em tempo real

Ver resultados de pesquisas

Comunicar com o assistente de IA

Consultar backlinks num painel lateral

Usar botões para importar, guardar, configurar e processar notas

#Testes

A aplicação foi testada com:

Testes unitários com pytest

Testes de integração que cobrem o ciclo completo (importar, guardar, pesquisar)

Testes de desempenho (tempo para criar links e extrair conceitos)

Testes manuais da interface (documentado em PDF)

#Requisitos
Python 3.9 ou superior

PyQt5

spaCy (modelo pt_core_news_sm)

FAISS

sentence-transformers

Ollama (opcional, apenas para o assistente de IA)

#Como executar
python main.py
