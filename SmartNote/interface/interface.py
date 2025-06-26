#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: interface.py
Descrição: Interface principal do SmartNote com PyQt5, integrando os módulos
           de IA, RAG, importação, backlinks e extração de conceitos.
===============================================================================
"""

import sys
import os

from typing import List, Dict

from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QTextEdit, QLabel, QLineEdit, QListWidget, QWidget, QMessageBox,
    QDialog, QInputDialog, QTabWidget, QCheckBox, QComboBox, QSplitter, 
    QGroupBox, QSpinBox, QDoubleSpinBox, QTextBrowser, QListWidgetItem, 
    QApplication, QSizePolicy, QShortcut,)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat, QKeySequence

# ==============================================================================
# Módulos Locais
# ==============================================================================

from modulos.configuracao import configurador
from modulos.conceitos import extrator_conceitos
from modulos.assistente_ia import assistente_ia
from modulos.links_semanticos import gerador_links
from modulos.importacao import importar_diretorio
from modulos.gravacao import gravador_notas
from modulos.busca import buscador_textual
from modulos.gerador_links import LinkSugerido, gerador_links_avancado
from modulos.backlinks import GestorBacklinks, PainelBacklinks

# ==============================================================================
# Diálogo de Importação
# ==============================================================================

class DialogoImportacao(QDialog):
    """
    Diálogo para seleção de diretório e importação de notas do sistema de ficheiros.

    Args:
        parent (QWidget, opcional): Janela pai do diálogo.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importação de Notas")
        self.setGeometry(200, 200, 500, 100)
        self.notas_importadas = []
        self.initUI()

    def initUI(self):
        """
        Inicializa a interface do diálogo de importação.
        """
        layout = QVBoxLayout()

        # Campo de seleção de diretório
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_button = QPushButton("Selecionar Diretório")
        self.dir_button.clicked.connect(self.selecionar_diretorio)

        dir_layout.addWidget(QLabel("Diretório:"))
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_button)

        layout.addLayout(dir_layout)

        # Botões de ação: importar ou cancelar
        buttons_layout = QHBoxLayout()

        self.importar_diretorio_button = QPushButton("Importar Notas")
        self.importar_diretorio_button.clicked.connect(self.importar_diretorio)
        buttons_layout.addWidget(self.importar_diretorio_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)


# ==============================================================================
# Métodos da Classe DialogoImportacao
# ==============================================================================

    def selecionar_diretorio(self):
        """
        Abre um diálogo para o utilizador selecionar um diretório de notas.
        """
        diretorio = QFileDialog.getExistingDirectory(self, "Selecionar Diretório de Notas")
        if diretorio:
            self.dir_input.setText(diretorio)

    def importar_diretorio(self):
        """
        Realiza a importação das notas a partir do diretório especificado.

        Atualiza o sistema com os novos ficheiros, recarrega os dados e reindexa.
        """
        diretorio = self.dir_input.text()

        if not diretorio:
            QMessageBox.warning(self, "Aviso", "Selecione um diretório primeiro!")
            return

        notas, erros = importar_diretorio(diretorio)

        if erros:
            QMessageBox.warning(self, "Erros na Importação", "\n".join(erros))

        if not notas:
            QMessageBox.information(self, "Importação", "Nenhuma nota foi importada.")
            return

        # Atualizar o diretório base para gravação
        diretorio_base = os.path.dirname(notas[0].caminho)
        gravador_notas.diretorio_notas = diretorio_base

        # Adicionar as notas importadas ao sistema principal
        for nota in notas:
            self.parent().arquivos.append({
                'titulo': nota.titulo,
                'conteudo': nota.conteudo,
                'caminho': nota.caminho
            })

        # Atualizar interface e sistema de busca/backlinks
        self.parent().atualizar_lista_notas()
        self.parent().reindexar_notas()

        # Feedback visual
        self.parent().statusBar().showMessage(
            f"{len(notas)} nota(s) importada(s) com sucesso.", 5000
        )

        self.accept()


# ==============================================================================
# Classe DialogoConfiguracoes
# ==============================================================================
class DialogoConfiguracoes(QDialog):
    """
    Diálogo de configurações avançadas para o SmartNote.
    Permite ao utilizador ajustar preferências do sistema.
    """

    def __init__(self, parent=None):
        """
        Inicializa o diálogo e configura a interface gráfica.

        Args:
            parent (QWidget, optional): Janela pai.
        """
        super().__init__(parent)
        self.setWindowTitle("Configurações do SmartNote")
        self.setGeometry(200, 200, 600, 300)
        self.initUI()

    def initUI(self):
        """
        Constrói a interface com múltiplas abas de configuração.
        """
        layout = QVBoxLayout()
        tabs = QTabWidget()

        # Abas de configuração
        tab_ia = self._criar_tab_ia()
        tabs.addTab(tab_ia, "Assistente IA")

        tab_rag = self._criar_tab_rag()
        tabs.addTab(tab_rag, "RAG")

        tab_links = self._criar_tab_links()
        tabs.addTab(tab_links, "Links Semânticos")

        tab_stopwords = self._criar_tab_stopwords()
        tabs.addTab(tab_stopwords, "Stopwords")

        tab_busca = self._criar_tab_busca()
        tabs.addTab(tab_busca, "Busca")

        tab_interface = self._criar_tab_interface()
        tabs.addTab(tab_interface, "Interface")

        layout.addWidget(tabs)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.salvar_configuracoes)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)

        self.reset_button = QPushButton("Restaurar Padrão")
        self.reset_button.clicked.connect(self.restaurar_padrao)

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.reset_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        # Carregar as configurações atuais ao abrir
        self.carregar_configuracoes()


    # ==============================================================================
    # Métodos de Criação das Abas de Configuração (RAG e IA)
    # ==============================================================================

    def _criar_tab_rag(self) -> QWidget:
        """
        Cria a aba de configurações do sistema RAG (Retrieval-Augmented Generation).

        Returns:
            QWidget: Aba com campos de configuração para o RAG.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        rag_group = QGroupBox("Configurações RAG")
        rag_layout = QVBoxLayout()

        # Limiar de relevância
        self.limiar_relevancia = QDoubleSpinBox()
        self.limiar_relevancia.setRange(0.0, 1.0)
        self.limiar_relevancia.setSingleStep(0.05)
        rag_layout.addWidget(QLabel("Limiar de Relevância:"))
        rag_layout.addWidget(self.limiar_relevancia)

        # Máximo de documentos no contexto
        self.max_documentos = QSpinBox()
        self.max_documentos.setRange(1, 20)
        rag_layout.addWidget(QLabel("Máx. Documentos no Contexto:"))
        rag_layout.addWidget(self.max_documentos)

        # Máximo de caracteres no contexto
        self.max_caracteres = QSpinBox()
        self.max_caracteres.setRange(500, 10000)
        self.max_caracteres.setSingleStep(500)
        rag_layout.addWidget(QLabel("Máx. Caracteres no Contexto:"))
        rag_layout.addWidget(self.max_caracteres)

        rag_group.setLayout(rag_layout)
        layout.addWidget(rag_group)

        widget.setLayout(layout)
        return widget


    def _criar_tab_ia(self) -> QWidget:
        """
        Cria a aba de configurações do assistente IA (Ollama).

        Returns:
            QWidget: Aba com opções para configurar o modelo de IA.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        modelo_group = QGroupBox("Modelo de IA")
        modelo_layout = QVBoxLayout()

        # Ativação da IA (checkbox)
        self.ativar_ollama = QCheckBox("Ativar Ollama")
        modelo_layout.addWidget(self.ativar_ollama)

        # Seleção de modelo IA (combobox)
        self.modelo_combo = QComboBox()
        self.modelo_combo.addItems(["gamma2", "tinyllama", "llama3"])
        modelo_layout.addWidget(QLabel("Modelo:"))
        modelo_layout.addWidget(self.modelo_combo)

        # Campo para URL do servidor Ollama
        self.url_ollama = QLineEdit()
        modelo_layout.addWidget(QLabel("URL Ollama:"))
        modelo_layout.addWidget(self.url_ollama)

        # Ajuste de temperatura (creatividade)
        self.temperatura = QDoubleSpinBox()
        self.temperatura.setRange(0.0, 2.0)
        self.temperatura.setSingleStep(0.1)
        modelo_layout.addWidget(QLabel("Temperatura:"))
        modelo_layout.addWidget(self.temperatura)

        modelo_group.setLayout(modelo_layout)
        layout.addWidget(modelo_group)

        widget.setLayout(layout)
        return widget


    # ==============================================================================
    # Aba de Configuração de Stopwords
    # ==============================================================================

    def _criar_tab_stopwords(self) -> QWidget:
        """
        Cria a aba de configuração de stopwords personalizadas.

        Returns:
            QWidget: Aba contendo a lista de stopwords e controles para adicionar/remover.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        self.lista_stopwords = QListWidget()
        self.lista_stopwords.addItems(configurador.obter_stopwords_personalizadas())
        layout.addWidget(self.lista_stopwords)

        form_layout = QHBoxLayout()
        self.input_stopword = QLineEdit()
        self.input_stopword.setPlaceholderText("Nova stopword...")

        btn_adicionar = QPushButton("Adicionar")
        btn_remover = QPushButton("Remover Selecionada")

        btn_adicionar.clicked.connect(self.adicionar_stopword)
        btn_remover.clicked.connect(self.remover_stopword)

        form_layout.addWidget(self.input_stopword)
        form_layout.addWidget(btn_adicionar)
        form_layout.addWidget(btn_remover)

        layout.addLayout(form_layout)
        widget.setLayout(layout)
        return widget


    def adicionar_stopword(self):
        """
        Adiciona uma nova stopword à lista, evitando duplicação.
        """
        palavra = self.input_stopword.text().strip().lower()
        existentes = [self.lista_stopwords.item(i).text() for i in range(self.lista_stopwords.count())]

        if palavra and palavra not in existentes:
            self.lista_stopwords.addItem(palavra)
            self.input_stopword.clear()


    def remover_stopword(self):
        """
        Remove a stopword atualmente selecionada na lista.
        """
        item = self.lista_stopwords.currentItem()
        if item:
            self.lista_stopwords.takeItem(self.lista_stopwords.row(item))


    def restaurar_stopwords_padrao(self):
        """
        Restaura as stopwords personalizadas com base na configuração global.
        Atualiza os módulos relevantes.
        """
        stopwords = configurador.obter_stopwords_personalizadas()
        self.lista_stopwords.clear()
        self.lista_stopwords.addItems(sorted(set(stopwords)))
        extrator_conceitos.adicionar_stopwords(stopwords)
        gerador_links_avancado.atualizar_stopwords_personalizadas(stopwords)


    # ==============================================================================
    # Aba de Configuração de Links Semânticos
    # ==============================================================================

    def _criar_tab_links(self) -> QWidget:
        """
        Cria a aba de configuração dos links semânticos.

        Returns:
            QWidget: Aba com campos para ajustar os critérios de links automáticos.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        links_group = QGroupBox("Links Semânticos")
        links_layout = QVBoxLayout()

        self.limiar_similaridade = QDoubleSpinBox()
        self.limiar_similaridade.setRange(0.0, 1.0)
        self.limiar_similaridade.setSingleStep(0.05)
        links_layout.addWidget(QLabel("Limiar de Similaridade:"))
        links_layout.addWidget(self.limiar_similaridade)

        self.max_links_paragrafo = QSpinBox()
        self.max_links_paragrafo.setRange(1, 10)
        links_layout.addWidget(QLabel("Máx. Links por Parágrafo:"))
        links_layout.addWidget(self.max_links_paragrafo)

        self.modo_semantico = QCheckBox("Ativar Modo Semântico")
        links_layout.addWidget(self.modo_semantico)

        links_group.setLayout(links_layout)
        layout.addWidget(links_group)

        widget.setLayout(layout)
        return widget


    # ==============================================================================
    # Aba de Configuração da Busca
    # ==============================================================================

    def _criar_tab_busca(self) -> QWidget:
        """
        Cria a aba de configuração de busca textual.

        Returns:
            QWidget: Aba com opções de busca, como acentuação e número máximo de resultados.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        busca_group = QGroupBox("Configurações de Busca")
        busca_layout = QVBoxLayout()

        self.ignorar_acentos = QCheckBox("Ignorar Acentos")
        busca_layout.addWidget(self.ignorar_acentos)

        self.max_resultados = QSpinBox()
        self.max_resultados.setRange(10, 200)
        busca_layout.addWidget(QLabel("Máx. Resultados:"))
        busca_layout.addWidget(self.max_resultados)

        busca_group.setLayout(busca_layout)
        layout.addWidget(busca_group)

        widget.setLayout(layout)
        return widget


    # ==============================================================================
    # Aba de Configuração da Interface
    # ==============================================================================

    def _criar_tab_interface(self) -> QWidget:
        """
        Cria a aba de personalização da interface do utilizador.

        Returns:
            QWidget: Aba com opções de fonte, visibilidade de painéis e autosave.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        interface_group = QGroupBox("Interface")
        interface_layout = QVBoxLayout()

        self.fonte_tamanho = QSpinBox()
        self.fonte_tamanho.setRange(5, 24)
        interface_layout.addWidget(QLabel("Tamanho da Fonte:"))
        interface_layout.addWidget(self.fonte_tamanho)

        self.negrito_fonte = QCheckBox("Texto em Negrito")
        interface_layout.addWidget(self.negrito_fonte)

        self.italico_fonte = QCheckBox("Texto em Itálico")
        interface_layout.addWidget(self.italico_fonte)

        self.mostrar_backlinks = QCheckBox("Mostrar Painel de Backlinks")
        interface_layout.addWidget(self.mostrar_backlinks)

        self.auto_salvar = QCheckBox("Auto-salvar")
        interface_layout.addWidget(self.auto_salvar)

        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)

        widget.setLayout(layout)
        return widget

    
    # ==============================================================================
    # Carregamento e Salvamento das Configurações
    # ==============================================================================

    def carregar_configuracoes(self):
        """
        Carrega as configurações atuais do sistema nos controlos da interface gráfica.
        """
        # IA
        modelo_ia = configurador.obter_modelo_ia()
        self.modelo_combo.setCurrentText(modelo_ia.get('nome', 'gamma2'))
        self.url_ollama.setText(modelo_ia.get('url_ollama', 'http://localhost:11434'))
        self.temperatura.setValue(modelo_ia.get('temperatura', 0.7))
        self.ativar_ollama.setChecked(configurador.obter("modelo_ia", "ativar_ollama", True))

        # RAG
        config_rag = configurador.obter_config_rag()
        self.limiar_relevancia.setValue(config_rag.get('limiar_relevancia', 0.3))
        self.max_documentos.setValue(config_rag.get('max_documentos_contexto', 5))
        self.max_caracteres.setValue(config_rag.get('max_caracteres_contexto', 3000))

        # Links Semânticos
        config_links = configurador.obter_config_links()
        self.limiar_similaridade.setValue(config_links.get('limiar_similaridade', 0.50))
        self.max_links_paragrafo.setValue(config_links.get('max_links_por_paragrafo', 3))
        self.modo_semantico.setChecked(config_links.get('modo_semantico_ativo', True))

        # Busca
        config_busca = configurador.obter_config_busca()
        self.ignorar_acentos.setChecked(config_busca.get('ignorar_acentos', True))
        self.max_resultados.setValue(config_busca.get('max_resultados', 50))

        # Interface
        config_interface = configurador.obter_config_interface()
        self.fonte_tamanho.setValue(config_interface.get('fonte_tamanho', 12))
        self.mostrar_backlinks.setChecked(config_interface.get('mostrar_backlinks', True))
        self.auto_salvar.setChecked(config_interface.get('auto_salvar', False))
        self.negrito_fonte.setChecked(config_interface.get('texto_negrito', False))
        self.italico_fonte.setChecked(config_interface.get('texto_italico', False))


    def salvar_configuracoes(self):
        """
        Salva as configurações atuais da interface nos ficheiros do sistema.
        """
        # IA
        configurador.definir('modelo_ia', 'nome', self.modelo_combo.currentText())
        configurador.definir('modelo_ia', 'url_ollama', self.url_ollama.text())
        configurador.definir('modelo_ia', 'temperatura', self.temperatura.value())
        configurador.definir('modelo_ia', 'ativar_ollama', self.ativar_ollama.isChecked())

        # RAG
        configurador.definir('rag', 'limiar_relevancia', self.limiar_relevancia.value())
        configurador.definir('rag', 'max_documentos_contexto', self.max_documentos.value())
        configurador.definir('rag', 'max_caracteres_contexto', self.max_caracteres.value())

        # Links Semânticos
        configurador.definir('links', 'limiar_similaridade', self.limiar_similaridade.value())
        configurador.definir('links', 'max_links_por_paragrafo', self.max_links_paragrafo.value())
        configurador.definir('links', 'modo_semantico_ativo', self.modo_semantico.isChecked())

        # Stopwords personalizadas
        stopwords = [self.lista_stopwords.item(i).text() for i in range(self.lista_stopwords.count())]
        configurador.salvar_stopwords_personalizadas(stopwords)
        extrator_conceitos.adicionar_stopwords(stopwords)
        gerador_links_avancado.atualizar_stopwords_personalizadas(stopwords)

        # Busca
        configurador.definir('busca', 'ignorar_acentos', self.ignorar_acentos.isChecked())
        configurador.definir('busca', 'max_resultados', self.max_resultados.value())

        # Interface
        configurador.definir('interface', 'fonte_tamanho', self.fonte_tamanho.value())
        configurador.definir('interface', 'mostrar_backlinks', self.mostrar_backlinks.isChecked())
        configurador.definir('interface', 'auto_salvar', self.auto_salvar.isChecked())
        configurador.definir('interface', 'texto_negrito', self.negrito_fonte.isChecked())
        configurador.definir('interface', 'texto_italico', self.italico_fonte.isChecked())

        # Persistência em ficheiro
        if configurador.salvar_configuracoes():
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", "Erro ao salvar configurações!")

    
    # ==============================================================================
    # Restaurar Configurações e Barra de Resultados de Busca
    # ==============================================================================

    def restaurar_padrao(self):
        """
        Restaura todas as configurações para os valores padrão após confirmação do utilizador.
        """
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "Restaurar todas as configurações para os valores padrão?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            configurador.resetar_para_padrao()
            self.carregar_configuracoes()


# ==============================================================================
# Barra de Resultados de Busca (Popup)
# ==============================================================================

class BarraResultadosDialog(QDialog):
    """
    Diálogo flutuante que exibe o estado da navegação entre resultados de busca.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool)
        self.setWindowTitle("Resultados da Busca")
        self.setFixedHeight(50)

        layout = QHBoxLayout()

        self.label_status = QLabel("0 de 0")
        layout.addWidget(self.label_status)

        self.btn_anterior = QPushButton("⏮")
        self.btn_anterior.clicked.connect(parent.retroceder_resultado)
        layout.addWidget(self.btn_anterior)

        self.btn_seguinte = QPushButton("⏭")
        self.btn_seguinte.clicked.connect(parent.avancar_resultado)
        layout.addWidget(self.btn_seguinte)

        btn_fechar = QPushButton("❌")
        btn_fechar.clicked.connect(self.fechar_popup)
        layout.addWidget(btn_fechar)

        self.setLayout(layout)


    def atualizar_total(self, total: int, atual: int):
        """
        Atualiza o contador visual de resultados.

        Args:
            total (int): Total de resultados
            atual (int): Índice do resultado atual (zero-based)
        """
        if total == 0:
            self.label_status.setText("0 de 0")
        else:
            self.label_status.setText(f"{atual + 1} de {total}")

    def fechar_popup(self):
        """
        Fecha o popup de resultados e remove o realce da nota principal.
        """
        self.hide()
        self.parent().remover_realce()


# ==============================================================================
# Classe Principal da Aplicação - SmartNoteApp
# ==============================================================================

class SmartNoteApp(QMainWindow):
    """
    Janela principal da aplicação SmartNote.
    Integra interface PyQt5 com funcionalidades como IA, backlinks, e busca.
    """

    def __init__(self):
        super().__init__()

        self.arquivos = []
        self.nota_atual = None
        self.resultados_busca = []
        self.indice_atual = -1

        # Inicializar gestor de backlinks antes da interface
        self.gestor_backlinks = GestorBacklinks()

        # Criar popup flutuante de resultados de busca
        self.popup_resultados = BarraResultadosDialog(self)

        # Inicializar UI e configurações
        self.initUI()
        self.configurar_aplicacao()

        # Conectar sinal de painel de backlinks
        if self.painel_backlinks:
            self.painel_backlinks.abrir_nota_solicitada.connect(self.abrir_nota_por_titulo)

        self.setWindowTitle('SmartNote')
        self.setGeometry(100, 100, 1400, 900)

    # ==============================================================================
    # Inicialização da Interface
    # ==============================================================================

    def initUI(self):
        """
        Configura a interface com layout principal e menus.
        """
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        main_splitter = QSplitter(Qt.Horizontal)

        # Painéis: esquerdo (lista), central (editor), direito (IA/backlinks)
        left_panel = self._criar_painel_esquerdo()
        center_panel = self._criar_painel_central()
        right_panel = self._criar_painel_direito()

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 700, 300])

        main_layout.addWidget(main_splitter)

        # Barras de menu e status
        self._criar_menu_bar()
        self.statusBar().showMessage("SmartNote carregado")

    def abrir_configuracoes(self):
        """
        Abre o diálogo de configurações e aplica alterações se aceitas.
        """
        dialogo = DialogoConfiguracoes(self)
        if dialogo.exec_() == QDialog.Accepted:
            self.configurar_aplicacao()
            assistente_ia.recarregar_configuracoes()


    # ==============================================================================
    # Painel Esquerdo - Lista de Notas
    # ==============================================================================

    def _criar_painel_esquerdo(self) -> QWidget:
        """
        Cria painel esquerdo com lista de notas e barra de busca.

        Returns:
            QWidget: Painel esquerdo com lista de notas
        """
        widget = QWidget()
        layout = QVBoxLayout()

        titulo = QLabel("Notas")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)

        self.busca_rapida = QLineEdit()
        self.busca_rapida.setPlaceholderText("Buscar notas...")
        self.busca_rapida.textChanged.connect(self.filtrar_notas)
        layout.addWidget(self.busca_rapida)

        self.notas_list = QListWidget()
        self.notas_list.itemClicked.connect(self.exibir_conteudo_da_nota)
        layout.addWidget(self.notas_list)

        buttons_layout = QVBoxLayout()
        layout.addLayout(buttons_layout)

        widget.setLayout(layout)
        return widget


    # ==============================================================================
    # Painel Central - Editor da Nota
    # ==============================================================================

    def _criar_painel_central(self) -> QWidget:
        """
        Cria painel central com editor de texto e barra de ações.

        Returns:
            QWidget: Painel com editor de nota e ferramentas
        """
        widget = QWidget()
        self.layout_editor = QVBoxLayout()

        # Toolbar da nota (título + busca avançada)
        toolbar_layout = QHBoxLayout()

        self.titulo_nota_label = QLabel("Selecione uma nota")
        self.titulo_nota_label.setFont(QFont("Arial", 16, QFont.Bold))
        toolbar_layout.addWidget(self.titulo_nota_label)
        toolbar_layout.addStretch()

        # Atalhos de formatação
        atalho_negrito = QShortcut(QKeySequence("Ctrl+N"), self)
        atalho_negrito.activated.connect(self.toggle_negrito)

        atalho_italico = QShortcut(QKeySequence("Ctrl+I"), self)
        atalho_italico.activated.connect(self.toggle_italico)

        self.busca_avancada = QLineEdit()
        self.busca_avancada.setPlaceholderText("Digite termo...")
        self.btn_buscar = QPushButton("🔍")
        self.btn_buscar.clicked.connect(lambda: self.executar_busca(self.busca_avancada.text()))

        toolbar_layout.addWidget(self.busca_avancada)
        toolbar_layout.addWidget(self.btn_buscar)

        self.layout_editor.addLayout(toolbar_layout)

        # Área de texto
        self.text_area = QTextEdit()
        self.text_area.textChanged.connect(self.marcar_nota_modificada)
        self.layout_editor.addWidget(self.text_area)

        # Barra inferior de ações
        actions_layout = QHBoxLayout()
        self.btn_processar_links = QPushButton("🔗 Processar Links")
        self.btn_processar_links.clicked.connect(self.processar_links_semanticos)
        actions_layout.addWidget(self.btn_processar_links)
        actions_layout.addStretch()

        self.layout_editor.addLayout(actions_layout)
        widget.setLayout(self.layout_editor)
        return widget


    # ==============================================================================
    # Funções de Estilo e Formatação de Texto
    # ==============================================================================

    def toggle_negrito(self):
        """
        Alterna o formato de negrito no texto selecionado ou no cursor atual.
        """
        cursor = self.text_area.textCursor()

        fmt = cursor.charFormat() if cursor.hasSelection() else self.text_area.currentCharFormat()
        current_weight = fmt.fontWeight()
        new_weight = QFont.Normal if current_weight == QFont.Bold else QFont.Bold
        fmt.setFontWeight(new_weight)

        cursor.mergeCharFormat(fmt)
        self.text_area.setTextCursor(cursor)


    def toggle_italico(self):
        """
        Alterna o formato de itálico no texto selecionado ou no cursor atual.
        """
        cursor = self.text_area.textCursor()

        fmt = cursor.charFormat() if cursor.hasSelection() else self.text_area.currentCharFormat()
        current_italic = fmt.fontItalic()
        fmt.setFontItalic(not current_italic)

        cursor.mergeCharFormat(fmt)
        self.text_area.setTextCursor(cursor)


    # ==============================================================================
    # Painel Direito (IA e Backlinks)
    # ==============================================================================

    def importar_diretorio(self):
        """
        Abre o diálogo de importação de diretório contendo notas.
        """
        dialogo = DialogoImportacao(self)
        dialogo.exec_()


    def _criar_painel_direito(self) -> QWidget:
        """
        Cria o painel direito com abas para backlinks e assistente IA.

        Returns:
            QWidget: Painel lateral com funcionalidades auxiliares
        """
        widget = QWidget()
        layout = QVBoxLayout()

        tabs = QTabWidget()

        # Verificar se o painel de backlinks deve ser exibido
        config_interface = configurador.obter_config_interface()
        self.painel_backlinks = None

        if config_interface.get('mostrar_backlinks', True):
            self.painel_backlinks = PainelBacklinks(self.gestor_backlinks, self)
            tabs.addTab(self.painel_backlinks, "Backlinks")

        # Aba do assistente IA (sempre presente)
        tab_ia = self._criar_tab_ia()
        tabs.addTab(tab_ia, "Assistente IA")

        layout.addWidget(tabs)
        widget.setLayout(layout)
        return widget


    # ==============================================================================
    # Manipulação de Notas
    # ==============================================================================

    def remover_nota(self, nota: Dict):
        """
        Remove uma nota com confirmação se não estiver guardada em disco.

        Args:
            nota (Dict): Nota a ser removida
        """
        if not nota:
            return

        guardada = 'caminho' in nota and os.path.exists(nota['caminho'])

        if not guardada:
            resposta = QMessageBox.question(
                self,
                "Nota não guardada",
                f"A nota '{nota['titulo']}' ainda não foi guardada.\nDeseja removê-la mesmo assim?",
                QMessageBox.Yes | QMessageBox.No
            )
            if resposta != QMessageBox.Yes:
                return

        # Remover da lista
        if nota in self.arquivos:
            self.arquivos.remove(nota)

        self.atualizar_lista_notas()

        # Limpar painel se a nota aberta for a removida
        if self.nota_atual == nota:
            self.nota_atual = None
            self.text_area.clear()
            self.titulo_nota_label.setText("Selecione uma nota")

        
    # ==============================================================================
    # Assistente IA - Aba e Configuração
    # ==============================================================================

    def _criar_tab_ia(self) -> QWidget:
        """
        Cria a aba do assistente IA com seleção de contexto e área de conversa.

        Returns:
            QWidget: Aba com interface do assistente IA.
        """
        widget = QWidget()
        layout = QVBoxLayout()

        # Seleção de contexto (nota atual ou todas)
        contexto_layout = QHBoxLayout()
        contexto_layout.addWidget(QLabel("Contexto:"))

        self.contexto_combo = QComboBox()
        self.contexto_combo.addItem("📄 Nota Atual")
        self.contexto_combo.addItem("🗂️ Todas as Notas")
        contexto_layout.addWidget(self.contexto_combo)

        layout.addLayout(contexto_layout)

        # Histórico de conversa
        self.ia_conversa = QTextBrowser()
        layout.addWidget(self.ia_conversa)

        # Campo de input
        self.ia_input = QLineEdit()
        self.ia_input.setPlaceholderText("Faça uma pergunta sobre as notas...")
        self.ia_input.returnPressed.connect(self.perguntar_ia)
        layout.addWidget(self.ia_input)

        # Botão de envio
        self.btn_ia = QPushButton("🤖 Perguntar")
        self.btn_ia.clicked.connect(self.perguntar_ia)
        layout.addWidget(self.btn_ia)

        widget.setLayout(layout)
        return widget


    # ==============================================================================
    # Menu Principal da Interface
    # ==============================================================================

    def _criar_menu_bar(self):
        """
        Cria a barra de menu superior com as opções principais da aplicação.
        """
        menubar = self.menuBar()

        # Menu Arquivo
        arquivo_menu = menubar.addMenu('Arquivo')
        arquivo_menu.addAction('Importar Notas', self.importar_diretorio)
        arquivo_menu.addAction('Guardar', self.salvar_nota_atual)
        arquivo_menu.addAction('Guardar Como...', self.guardar_como)
        arquivo_menu.addAction('Guardar Tudo', self.salvar_todas_notas)
        arquivo_menu.addAction('Nova Nota', self.criar_nova_nota)
        arquivo_menu.addSeparator()
        arquivo_menu.addAction('Sair', self.close)

        # Menu Ferramentas
        ferramentas_menu = menubar.addMenu('Ferramentas')
        ferramentas_menu.addAction('Processar Links', self.processar_links_semanticos)
        ferramentas_menu.addAction('Sincronizar Conteúdo', self.reindexar_notas)
        ferramentas_menu.addAction('Configurações', self.abrir_configuracoes)

        # Menu Ajuda
        ajuda_menu = menubar.addMenu('Ajuda')
        ajuda_menu.addAction('Sobre', self.mostrar_sobre)


    # ==============================================================================
    # Configuração Inicial da Aplicação
    # ==============================================================================

    def configurar_aplicacao(self):
        """
        Aplica as configurações da aplicação com base nas preferências guardadas.
        """

        # Interface
        config_interface = configurador.obter_config_interface()

        fonte = QFont("Arial", config_interface.get('fonte_tamanho', 12))
        fonte.setBold(config_interface.get('texto_negrito', False))
        fonte.setItalic(config_interface.get('texto_italico', False))
        self.text_area.setFont(fonte)

        # Configurações de busca
        self.config_busca = configurador.obter_config_busca()

        # Configurações de links semânticos
        config_links = configurador.obter_config_links()
        gerador_links.configurar_parametros(
            limiar_similaridade=config_links.get('limiar_similaridade', 0.15),
            max_links_por_paragrafo=config_links.get('max_links_por_paragrafo', 3),
            modo_semantico=config_links.get('modo_semantico_ativo', True)
        )

        # Assistente IA
        config_ia = configurador.obter_modelo_ia()

        if not config_ia.get('ativar_ollama', True):
            print("[INFO] Ollama desativado nas configurações.")
            return

        # Aplicar configurações ao assistente IA
        assistente_ia.url_ollama = config_ia.get('url_ollama', 'http://localhost:11434')
        assistente_ia.modelo_ia = config_ia.get('nome', 'gamma2')
        assistente_ia.max_tokens = config_ia.get('max_tokens', 2048)
        assistente_ia.temperatura = config_ia.get('temperatura', 0.7)
        assistente_ia.timeout = config_ia.get('timeout', 30)

        assistente_ia.recarregar_configuracoes()


    # ==============================================================================
    # Realce de Termos na Nota
    # ==============================================================================

    def realcar_termo_na_nota(self, termo: str):
        """
        Realça todas as ocorrências de um termo na nota atual.

        Args:
            termo (str): Termo a ser realçado no conteúdo da nota.
        """
        if not self.nota_atual:
            return

        # Limpar realces anteriores
        self.remover_realce()

        documento = self.text_area.document()
        cursor = documento.find(termo, 0)

        # Formato de destaque
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FFD700"))  # Cor amarela ouro
        fmt.setFontWeight(QFont.Bold)

        # Aplicar realce em todas as ocorrências
        while not cursor.isNull():
            cursor.mergeCharFormat(fmt)
            cursor = documento.find(termo, cursor.position())

        # Focar na primeira ocorrência
        primeira_ocorrencia = documento.find(termo, 0)
        if not primeira_ocorrencia.isNull():
            self.text_area.setTextCursor(primeira_ocorrencia)


    # ==============================================================================
    # Processamento de Links Semânticos
    # ==============================================================================

    def processar_links_semanticos(self):
        """
        Processa e sugere links semânticos entre as notas carregadas.

        Mostra uma pré-visualização interativa dos links encontrados.
        """
        if not self.arquivos:
            QMessageBox.warning(self, "Aviso", "Nenhuma nota carregada!")
            return

        try:
            # Criar índice semântico se ainda não existir
            if not gerador_links.indice_titulos:
                QMessageBox.information(self, "Info", "Criando índice semântico... Isso pode demorar alguns segundos.")
                sucesso = gerador_links.criar_indice_titulos(self.arquivos)
                if not sucesso:
                    QMessageBox.critical(self, "Erro", "Falha ao criar índice semântico. Verifique as dependências.")
                    return

            # Gerar links sugeridos entre notas
            gerador_links.modo_semantico_ativo = True
            links_sugeridos = gerador_links.gerar_links_sugeridos(self.arquivos)

            # Remover links para a própria nota
            for titulo, links in links_sugeridos.items():
                links_sugeridos[titulo] = [l for l in links if l.nota_destino != titulo]

            # Verificação final
            if not any(links_sugeridos.values()):
                QMessageBox.information(self, "Info", "Nenhum link sugerido encontrado.")
                return

            # Mostrar janela de pré-visualização
            self.mostrar_preview_links(links_sugeridos)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar links: {str(e)}")

    
    # ==============================================================================
    # Pré-visualização de Links Sugeridos
    # ==============================================================================

    def mostrar_preview_links(self, links_sugeridos: Dict[str, List[LinkSugerido]]):
        """
        Exibe uma janela com a pré-visualização dos links sugeridos.

        Permite filtrar entre links semânticos, literais ou ambos.

        Args:
            links_sugeridos (Dict[str, List[LinkSugerido]]): 
                Dicionário com os títulos das notas como chave 
                e listas de links sugeridos como valor.
        """
        config_links = configurador.obter_config_links()
        modo_semantico_ativo = config_links.get('modo_semantico_ativo', True)

        # Verifica se todos os links são semânticos
        apenas_semanticos = all(
            all(link.tipo == "semantico" for link in lista)
            for lista in links_sugeridos.values()
        )

        if not modo_semantico_ativo and apenas_semanticos:
            QMessageBox.information(
                self,
                "Info",
                "Modo semântico está desativado e não há links literais para visualizar."
            )
            return

        # Se o modo semântico estiver desativado, solicitar confirmação
        if not modo_semantico_ativo:
            resposta = QMessageBox.question(
                self,
                "Modo Semântico Desativado",
                "O modo semântico está desativado. Apenas links literais estarão disponíveis.\n\nDeseja continuar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if resposta != QMessageBox.Yes:
                return
    
        # Criar janela de diálogo
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Pré-visualização de Links")
        dialogo.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        # Filtro de tipo de link
        filtro_combo = QComboBox()
        filtro_combo.addItems(["Ambos", "Apenas Literais", "Apenas Semânticos"])
        filtro_combo.setCurrentIndex(0)
        layout.addWidget(filtro_combo)

        if not modo_semantico_ativo:
            # Desativar opções de semântica caso necessário
            filtro_combo.setCurrentIndex(1)
            filtro_combo.model().item(0).setEnabled(False)  # Ambos
            filtro_combo.model().item(2).setEnabled(False)  # Apenas Semânticos

        # Área de visualização de links
        preview_area = QTextBrowser()


    # ==============================================================================
    # Função de Pré-visualização de Links - Continuação
    # ==============================================================================

    def mostrar_preview_links(self, links_sugeridos: Dict[str, List[LinkSugerido]]):
        """
        Exibe a interface de pré-visualização de links sugeridos, 
        com opção de filtro e aplicação.

        Args:
            links_sugeridos (Dict[str, List[LinkSugerido]]): 
                Links gerados agrupados por título de nota.
        """
        config_links = configurador.obter_config_links()
        modo_semantico_ativo = config_links.get('modo_semantico_ativo', True)

        apenas_semanticos = all(
            all(link.tipo == "semantico" for link in lista)
            for lista in links_sugeridos.values()
        )

        if not modo_semantico_ativo and apenas_semanticos:
            QMessageBox.information(
                self,
                "Info",
                "Modo semântico está desativado e não há links literais para visualizar."
            )
            return

        if not modo_semantico_ativo:
            resposta = QMessageBox.question(
                self,
                "Modo Semântico Desativado",
                "O modo semântico está desativado. Apenas links literais estarão disponíveis.\n\nDeseja continuar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if resposta != QMessageBox.Yes:
                return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Pré-visualização de Links")
        dialogo.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()

        filtro_combo = QComboBox()
        filtro_combo.addItems(["Ambos", "Apenas Literais", "Apenas Semânticos"])
        filtro_combo.setCurrentIndex(0)
        layout.addWidget(filtro_combo)

        if not modo_semantico_ativo:
            filtro_combo.setCurrentIndex(1)
            filtro_combo.model().item(0).setEnabled(False)
            filtro_combo.model().item(2).setEnabled(False)

        preview_area = QTextBrowser()

        def atualizar_preview():
            """Atualiza a visualização HTML com base no filtro atual."""
            html = "<h2 style='margin-bottom:15px;'>Links Sugeridos</h2>"

            for nota_titulo, links in links_sugeridos.items():
                filtro = filtro_combo.currentText()

                # Filtragem por tipo de link
                links_filtrados = [
                    link for link in links
                    if (filtro == "Ambos") or
                    (filtro == "Apenas Literais" and link.tipo == "literal") or
                    (filtro == "Apenas Semânticos" and link.tipo == "semantico")
                ]

                if not links_filtrados:
                    continue

                html += f"<h3 style='color:#333;'>{nota_titulo}</h3>"

                for link in links_filtrados:
                    cor = "#ffffcc" if link.tipo == "literal" else "#d0f0ff"
                    rotulo = "🔗 Literal" if link.tipo == "literal" else "💡 Semântico"
                    link_md = f"[[{link.nota_destino}|{link.termo}]]"

                    html += f"""
                    <div style='margin: 8px 0; padding: 10px; background-color:{cor}; border-left: 5px solid #666;'>
                        <b>{rotulo}:</b> {link_md}<br>
                        <b>Confiança:</b> {link.score_similaridade:.2f}<br>
                        <b>Contexto:</b> <i>{link.contexto.strip()}</i>
                    </div>
                    """

            preview_area.setHtml(html)

        filtro_combo.currentIndexChanged.connect(atualizar_preview)
        atualizar_preview()

        layout.addWidget(preview_area)

        # Botões de ação
        buttons_layout = QHBoxLayout()

        btn_aplicar = QPushButton("Aplicar Links")
        btn_aplicar.clicked.connect(
            lambda: self.aplicar_links_sugeridos(
                links_sugeridos,
                dialogo,
                filtro_combo.currentText()
            )
        )

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialogo.reject)

        buttons_layout.addWidget(btn_aplicar)
        buttons_layout.addWidget(btn_cancelar)

        layout.addLayout(buttons_layout)
        dialogo.setLayout(layout)
        dialogo.exec_()


    # ==============================================================================
    # Aplicação de Links Sugeridos
    # ==============================================================================

    def aplicar_links_sugeridos(
        self,
        links_sugeridos: Dict[str, List[LinkSugerido]],
        dialogo: QDialog,
        filtro_tipo: str
    ):
        """
        Aplica links sugeridos no conteúdo das notas e atualiza backlinks.

        Args:
            links_sugeridos (Dict[str, List[LinkSugerido]]): 
                Dicionário com os links sugeridos por nota.
            dialogo (QDialog): 
                Diálogo de onde foi feita a chamada (será fechado se sucesso).
            filtro_tipo (str): 
                Tipo de link a aplicar ("Apenas Semânticos", "Apenas Literais", "Ambos").
        """
        try:
            links_aplicados = 0

            for nota in self.arquivos:
                titulo = nota['titulo']
                if titulo not in links_sugeridos:
                    continue

                links_nota = links_sugeridos[titulo]

                # Filtragem por tipo selecionado
                tipo_alvo = None
                if filtro_tipo == "Apenas Semânticos":
                    tipo_alvo = "semantico"
                elif filtro_tipo == "Apenas Literais":
                    tipo_alvo = "literal"

                if tipo_alvo:
                    links_nota = [l for l in links_nota if l.tipo.strip().lower() == tipo_alvo]

                if not links_nota:
                    continue

                # Separar links com e sem posição
                links_com_posicao = [
                    l for l in links_nota
                    if l.posicao_inicio >= 0 and l.posicao_fim > l.posicao_inicio
                ]
                links_sem_posicao = [
                    l for l in links_nota
                    if l.posicao_inicio < 0
                ]

                conteudo_original = nota['conteudo']
                novo_conteudo = gerador_links.aplicar_links_em_memoria(
                    conteudo_original, links_com_posicao
                )

                # Registar backlinks semânticos
                for link in links_nota:
                    if link.tipo.strip().lower() == "semantico":
                        self.gestor_backlinks.registrar_link_semantico(
                            origem=nota['titulo'],
                            destino=link.nota_destino,
                            termo=link.termo
                        )

                if novo_conteudo != conteudo_original:
                    nota['conteudo'] = novo_conteudo
                    links_aplicados += len(links_com_posicao)

                    # Atualizar nota atual visível
                    if self.nota_atual and nota['caminho'] == self.nota_atual['caminho']:
                        self.text_area.setPlainText(novo_conteudo)

                # Contabilizar links semânticos sem posição como "registrados"
                links_aplicados += len(links_sem_posicao)

            # Atualizar painel de backlinks se ativo
            if self.painel_backlinks:
                self.painel_backlinks.atualizar_backlinks(self.nota_atual)

            dialogo.accept()

            QMessageBox.information(
                self,
                "Sucesso",
                f"{links_aplicados} link(s) processado(s) com sucesso!\n"
                f"- {len(links_com_posicao)} aplicados no texto\n"
                f"- {len(links_sem_posicao)} registrados como conceitos relacionados"
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao aplicar links: {str(e)}")


    # ==============================================================================
    # Realce de Termos e Execução de Busca
    # ==============================================================================

    def realcar_termo_na_nota(self, termo: str):
        """
        Realça todas as ocorrências de um termo na nota atual.

        Args:
            termo (str): Termo a ser realçado.
        """
        if not self.nota_atual or not termo:
            return

        # Limpar realces anteriores
        cursor = self.text_area.textCursor()
        cursor.select(QTextCursor.Document)
        fmt_clear = QTextCharFormat()
        fmt_clear.setBackground(QColor("transparent"))
        cursor.mergeCharFormat(fmt_clear)

        # Aplicar novo realce
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FFFF00"))  # Amarelo
        fmt.setFontWeight(QFont.Bold)

        documento = self.text_area.document()
        cursor = documento.find(termo, 0)

        while not cursor.isNull():
            cursor.mergeCharFormat(fmt)
            cursor = documento.find(termo, cursor.position())

        # Posicionar na primeira ocorrência
        primeira = documento.find(termo, 0)
        if not primeira.isNull():
            self.text_area.setTextCursor(primeira)


    def executar_busca(self, termo: str):
        """
        Executa busca textual nas notas com base nas configurações.

        Args:
            termo (str): Termo de busca inserido pelo utilizador.
        """
        configuracao = {
            "ignorar_acentos": self.config_busca.get("ignorar_acentos", True),
            "diferenciar_maiusculas": self.config_busca.get("diferenciar_maiusculas", False),
            "modo_regex": self.config_busca.get("modo_regex", False),
            "usar_cache": self.config_busca.get("usar_cache", False)
        }

        self.resultados_busca = buscador_textual.buscar(termo, self.arquivos, configuracao)
        self.indice_atual = 0 if self.resultados_busca else -1

        if self.resultados_busca:
            self.ir_para_resultado_atual()
            self.popup_resultados.atualizar_total(len(self.resultados_busca), self.indice_atual)
            self.popup_resultados.show()
            self.statusBar().showMessage(f"{len(self.resultados_busca)} ocorrência(s) encontrada(s)")
        else:
            self.popup_resultados.hide()
            QMessageBox.information(self, "Busca", "Nenhuma ocorrência encontrada.")


    # ==============================================================================
    # Navegação de Resultados e Realce de Ocorrências
    # ==============================================================================

    def avancar_resultado(self):
        """
        Avança para o próximo resultado da busca.
        """
        if not self.resultados_busca:
            return

        self.indice_atual = (self.indice_atual + 1) % len(self.resultados_busca)
        self.ir_para_resultado_atual()


    def retroceder_resultado(self):
        """
        Retrocede para o resultado anterior da busca.
        """
        if not self.resultados_busca:
            return

        self.indice_atual = (self.indice_atual - 1) % len(self.resultados_busca)
        self.ir_para_resultado_atual()


    def selecionar_nota_na_lista(self, nota: dict):
        """
        Seleciona a nota correspondente na lista da interface.

        Args:
            nota (dict): Dicionário da nota a selecionar.
        """
        for i in range(self.notas_list.count()):
            item = self.notas_list.item(i)
            if item.data(Qt.UserRole).get("caminho") == nota.get("caminho"):
                self.notas_list.setCurrentItem(item)
                break


    def realcar_ocorrencia(self, posicao: int, tamanho: int):
        """
        Realça uma ocorrência específica de texto com base na posição e tamanho.

        Args:
            posicao (int): Posição inicial do termo.
            tamanho (int): Número de caracteres do termo.
        """
        self.remover_realce()

        cursor = self.text_area.textCursor()
        cursor.setPosition(posicao)
        cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor, tamanho)

        fmt = QTextCharFormat()
        fmt.setBackground(QColor("yellow"))
        fmt.setFontWeight(QFont.Bold)

        cursor.mergeCharFormat(fmt)
        self.text_area.setTextCursor(cursor)


    def remover_realce(self):
        """
        Remove todos os realces aplicados na área de texto.
        """
        cursor = self.text_area.textCursor()
        cursor.beginEditBlock()

        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)

        clear_format = QTextCharFormat()
        clear_format.setBackground(QColor("transparent"))
        clear_format.setFontWeight(QFont.Normal)

        cursor.mergeCharFormat(clear_format)
        cursor.endEditBlock()


    # ==============================================================================
    # Busca Avançada e Interação com Assistente IA
    # ==============================================================================

    def ir_para_resultado_atual(self):
        """
        Navega para o resultado de busca atual, exibindo e realçando o termo.
        """
        resultado = self.resultados_busca[self.indice_atual]

        for nota in self.arquivos:
            if nota.get("caminho") == resultado.caminho:
                self.nota_atual = nota
                self.text_area.setPlainText(nota["conteudo"])
                self.selecionar_nota_na_lista(nota)

                termo_busca = self.busca_avancada.text().strip()
                self.realcar_ocorrencia(resultado.posicoes[0], len(termo_busca))

                self.titulo_nota_label.setText(nota["titulo"])

                if self.painel_backlinks:
                    self.painel_backlinks.atualizar_backlinks(self.nota_atual)

                self.popup_resultados.atualizar_total(len(self.resultados_busca), self.indice_atual)
                break


    def perguntar_ia(self):
        """
        Envia uma pergunta ao assistente IA com base no contexto selecionado.

        Fluxo:
        - Verifica se há notas carregadas.
        - Garante que o Ollama está ativo.
        - Usa o contexto da nota atual ou de todas, conforme opção.
        - Mostra resposta no painel de conversa, incluindo documentos utilizados.
        """
        pergunta = self.ia_input.text().strip()
        if not pergunta:
            return

        if not self.arquivos:
            self.ia_conversa.append(
                "<p style='color: red;'><b>Aviso:</b> Nenhum conteúdo foi adicionado até ao momento.</p>"
            )
            self.btn_ia.setEnabled(True)
            return

        self.ia_input.clear()
        self.btn_ia.setEnabled(False)

        try:
            if not assistente_ia.testar_conexao_ollama():
                self.ia_conversa.append(
                    "<p style='color: red;'><b>Erro:</b> Ollama não está disponível. "
                    "Verifique se está em execução.</p>"
                )
                return

            # Determinar o contexto com base na seleção
            if self.contexto_combo.currentIndex() == 1:  # Todas as notas
                contexto = "CONTEXTO GERAL:\n"
                for nota in self.arquivos:
                    trecho = nota['conteudo'][:200].replace('\n', ' ').strip()
                    contexto += f"- {nota['titulo']}: {trecho}...\n"
            else:
                contexto = self.nota_atual['conteudo'] if self.nota_atual else ""

            max_contexto = assistente_ia.max_caracteres_contexto
            contexto = contexto[:max_contexto]

            # Gerar resposta via RAG
            resultado = assistente_ia.gerar_resposta_com_rag(pergunta, contexto)
            resposta = resultado['resposta']
            documentos_usados = resultado.get('documentos_usados', [])

            # Exibir pergunta e resposta
            self.ia_conversa.append(f"<p><b>Pergunta:</b> {pergunta}</p>")
            self.ia_conversa.append(f"<p><b>Resposta:</b> {resposta}</p>")

            # Exibir documentos utilizados no RAG
            if documentos_usados:
                docs_html = "<p><b>Documentos consultados:</b></p><ul>"
                for titulo in documentos_usados:
                    docs_html += f"<li>{titulo}</li>"
                docs_html += "</ul>"
                self.ia_conversa.append(docs_html)

            self.ia_conversa.append("<hr>")

        except Exception as e:
            self.ia_conversa.append(f"<p style='color: red;'><b>Erro:</b> {str(e)}</p>")

        finally:
            self.btn_ia.setEnabled(True)


    # ==============================================================================
    # Reindexação e Reconfiguração Dinâmica
    # ==============================================================================

    def reindexar_notas(self):
        """
        Reindexa todas as notas carregadas.

        Realiza:
        - Reconstrução do painel de backlinks.
        - Verificação de existência dos ficheiros.
        - Recriação dos índices semânticos (IA e links).
        - Remoção de backlinks inválidos.
        """
        # QTabWidget onde está o painel de backlinks
        tabs = self.findChild(QTabWidget)
        if tabs:
            index = tabs.indexOf(self.painel_backlinks)
            if index != -1:
                tabs.removeTab(index)
            self.painel_backlinks = PainelBacklinks(self.gestor_backlinks, self)
            tabs.insertTab(0, self.painel_backlinks, "Backlinks")

        if not self.arquivos:
            return

        try:
            self.statusBar().showMessage("Sincronizando conteúdo...")
            QApplication.processEvents()

            # 1. Remover notas cujos ficheiros foram eliminados
            self.arquivos = [n for n in self.arquivos if os.path.exists(n.get("caminho", ""))]

            # 2. Limpar nota atual se não existir
            if self.nota_atual and not os.path.exists(self.nota_atual.get("caminho", "")):
                self.nota_atual = None
                self.text_area.clear()
                self.titulo_nota_label.setText("Selecione uma nota")

            # 3. Atualizar índice do assistente IA
            assistente_ia.criar_indice_conteudo(self.arquivos)

            # 4. Atualizar índice do gerador de links
            gerador_links.criar_indice_titulos(self.arquivos)

            # 5. Remover backlinks obsoletos
            titulos_atuais = {n['titulo'] for n in self.arquivos}
            self.gestor_backlinks.remover_backlinks_invalidos(titulos_atuais)

            # 6. Atualizar backlinks da nota atual
            if self.nota_atual:
                self.painel_backlinks.atualizar_backlinks(self.nota_atual)

            self.statusBar().showMessage("Conteúdo sincronizado com sucesso!", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao sincronizar: {str(e)}")


    def recriar_painel_direito(self):
        """
        Reconstrói dinamicamente o painel direito com base nas configurações atuais.
        """
        splitter = self.centralWidget().layout().itemAt(0).widget()  # QSplitter

        # Remover o painel atual
        splitter.widget(2).deleteLater()

        # Criar novo painel
        novo_painel_direito = self._criar_painel_direito()
        splitter.insertWidget(2, novo_painel_direito)

        # Reestabelecer ligação ao painel de backlinks, se necessário
        if self.painel_backlinks:
            self.painel_backlinks.abrir_nota_solicitada.connect(self.abrir_nota_por_titulo)


    def abrir_configuracoes(self):
        """
        Abre o diálogo de configurações. Reaplica-as se forem aceites.
        """
        dialogo = DialogoConfiguracoes(self)
        if dialogo.exec_() == QDialog.Accepted:
            self.configurar_aplicacao()
            self.recriar_painel_direito()

    
    # ==============================================================================
    # Sobre e Atualização de Lista de Notas
    # ==============================================================================

    def mostrar_sobre(self):
        """
        Mostra o diálogo "Sobre" com informações da aplicação SmartNote.
        """
        QMessageBox.about(
            self,
            "Sobre o SmartNote",
            """
            <h3>SmartNote</h3>
            <p>O <b>SmartNote</b> é uma aplicação de anotações inteligente, segura, inspirada na filosofia de redes de conhecimento como o Obsidian, mas com recursos únicos de inteligência artificial.</p>

            <h4>Conceito Principal:</h4>
            <p>O SmartNote conecta automaticamente as suas notas através de dois tipos de ligações:</p>
            <ul>
                <li><b>Links literais:</b> Palavras ou expressões exatas entre diferentes notas.</li>
                <li><b>Links semânticos:</b> Relações de significado entre frases, mesmo com vocabulário distinto.</li>
            </ul>
            <p>Essas ligações criam um conhecimento interligado, permitindo navegação fluida entre ideias.</p>

            <h4>Recursos:</h4>
            <ul>
                <li>Links literais e semânticos automáticos</li>
                <li>Assistente IA local (RAG) para busca contextual</li>
                <li>Busca textual avançada por todas as notas</li>
                <li>Sistema de backlinks visível e clicável</li>
                <li>Importação automática de múltiplos arquivos</li>
            </ul>

            <p><b>Daniel Gonçalves, 2000065</b><br>
            Projeto de Engenharia Informática<br>
            Universidade Aberta, 2025</p>
            """
        )


    # ==============================================================================
    # Atualização da Lista de Notas (Painel Lateral)
    # ==============================================================================

    def atualizar_lista_notas(self):
        """
        Atualiza a lista visual de notas no painel esquerdo.
        Inclui botões para remover cada nota.
        """
        self.notas_list.clear()

        for nota in self.arquivos:
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)
            layout.setContentsMargins(5, 0, 5, 0)
            layout.setSpacing(5)

            # Label com título da nota
            label = QLabel(nota['titulo'])
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            label.setStyleSheet("color: black;")
            layout.addWidget(label)

            # Botão de remover nota
            btn_remover = QPushButton("❌")
            btn_remover.setFixedSize(20, 20)
            btn_remover.setStyleSheet("QPushButton { border: none; }")
            btn_remover.setToolTip("Remover nota")
            btn_remover.clicked.connect(lambda _, n=nota: self.remover_nota(n))
            layout.addWidget(btn_remover)

            # Inserir item na QListWidget
            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            item.setData(Qt.UserRole, nota)

            self.notas_list.addItem(item)
            self.notas_list.setItemWidget(item, item_widget)


    
    # ==============================================================================
    # Funções de Interação com Notas (Filtro, Exibição, Salvamento)
    # ==============================================================================

    def filtrar_notas(self):
        """
        Filtra as notas na lista com base no texto inserido na busca rápida.
        """
        filtro = self.busca_rapida.text().lower()
        for i in range(self.notas_list.count()):
            item = self.notas_list.item(i)
            item.setHidden(filtro not in item.data(Qt.UserRole).get("titulo", "").lower())


    def exibir_conteudo_da_nota(self, item):
        """
        Exibe o conteúdo da nota selecionada e atualiza o editor e o painel de backlinks.

        Args:
            item (QListWidgetItem): Item selecionado na lista de notas.
        """
        # Salvar alterações da nota anterior
        if self.nota_atual:
            self.nota_atual['conteudo'] = self.text_area.toPlainText()

        # Obter metadados do item e localizar a nota completa
        nota = item.data(Qt.UserRole)
        for n in self.arquivos:
            if n.get("caminho") == nota.get("caminho"):
                self.nota_atual = n
                break
        else:
            self.nota_atual = nota

        # Exibir conteúdo
        self.text_area.setPlainText(self.nota_atual["conteudo"])
        self.titulo_nota_label.setText(self.nota_atual["titulo"])

        # Atualizar backlinks
        if self.painel_backlinks:
            self.painel_backlinks.atualizar_backlinks(self.nota_atual)


    def marcar_nota_modificada(self):
        """
        Marca a nota atual como modificada, atualizando seu conteúdo.
        """
        if self.nota_atual:
            self.nota_atual['conteudo'] = self.text_area.toPlainText()


    def salvar_nota_atual(self):
        """
        Salva a nota atualmente aberta no editor.
        """
        if not self.nota_atual:
            return

        sucesso, erro = gravador_notas.gravar_nota_individual(self.nota_atual)
        if sucesso:
            self.statusBar().showMessage("Nota salva com sucesso", 3000)
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao guardar nota: {erro}")


    def guardar_como(self):
        """
        Abre diálogo para guardar a nota atual num local específico definido pelo utilizador.
        """
        if not self.nota_atual:
            QMessageBox.warning(self, "Aviso", "Nenhuma nota selecionada.")
            return

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Como...",
            f"{self.nota_atual['titulo']}.md",
            "Markdown (*.md);;Texto (*.txt);;Todos os arquivos (*)"
        )

        if caminho:
            sucesso, erro = gravador_notas.guardar_nota_em_caminho(self.nota_atual, caminho)

            if sucesso:
                self.nota_atual['caminho'] = caminho
                self.statusBar().showMessage("Nota salva com sucesso", 3000)
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao guardar nota: {erro}")


    def salvar_todas_notas(self):
        """
        Salva todas as notas abertas no sistema, incluindo a atual visível.
        """
        if self.nota_atual:
            self.nota_atual["conteudo"] = self.text_area.toPlainText()
            for idx, nota in enumerate(self.arquivos):
                if nota.get("caminho") == self.nota_atual.get("caminho"):
                    self.arquivos[idx]["conteudo"] = self.nota_atual["conteudo"]
                    break

        # Verificação de integridade
        for nota in self.arquivos:
            if 'caminho' not in nota or not nota['caminho']:
                print(f"[ERRO] Nota sem caminho: {nota.get('titulo')}")
            if 'conteudo' not in nota:
                print(f"[ERRO] Nota sem conteúdo: {nota.get('titulo')}")

        resultado = gravador_notas.gravar_notas_lote(self.arquivos)

        if resultado['erros']:
            self.statusBar().showMessage("Algumas notas não foram guardadas", 5000)
        else:
            self.statusBar().showMessage("Todas as notas foram guardadas com sucesso", 3000)


    # ==============================================================================
    # Criação e Abertura de Notas
    # ==============================================================================

    def criar_nova_nota(self):
        """
        Cria uma nova nota a partir de um título fornecido pelo utilizador.
        """
        titulo, ok = QInputDialog.getText(self, "Nova Nota", "Título da nota:")
        if ok and titulo:
            nome_ficheiro = f"{titulo}.md"
            caminho_completo = os.path.join(gravador_notas.diretorio_notas, nome_ficheiro)

            nova_nota = {
                'titulo': titulo,
                'conteudo': f"# {titulo}\n\n",
                'caminho': caminho_completo
            }

            self.arquivos.append(nova_nota)
            self.atualizar_lista_notas()
            self.reindexar_notas()

            # Seleciona automaticamente a nova nota criada
            for i in range(self.notas_list.count()):
                item = self.notas_list.item(i)
                if item.data(Qt.UserRole) == nova_nota:
                    self.notas_list.setCurrentItem(item)
                    self.exibir_conteudo_da_nota(item)
                    break


    def abrir_nota_por_titulo(self, titulo: str):
        """
        Abre uma nota com base no título especificado.

        Args:
            titulo (str): Título da nota a ser aberta.
        """
        # 1. Procurar na lista visível (filtrada)
        for i in range(self.notas_list.count()):
            item = self.notas_list.item(i)
            if not item.isHidden():
                nota = item.data(Qt.UserRole)
                if nota['titulo'] == titulo:
                    self.notas_list.setCurrentItem(item)
                    self.exibir_conteudo_da_nota(item)
                    return

        # 2. Procurar em toda a lista (fallback)
        for i in range(self.notas_list.count()):
            item = self.notas_list.item(i)
            nota = item.data(Qt.UserRole)
            if nota['titulo'] == titulo:
                self.notas_list.setCurrentItem(item)
                self.exibir_conteudo_da_nota(item)
                return

        # 3. Caso não encontrada
        QMessageBox.information(self, "Nota não encontrada",
                                f"A nota '{titulo}' não foi encontrada na lista.")


# ==============================================================================
# Execução Principal da Aplicação
# ==============================================================================

def executar_smartnote():
    """
    Executa a aplicação SmartNote com interface.
    """
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    janela = SmartNoteApp()
    janela.show()

    sys.exit(app.exec_())


# ==============================================================================
# Ponto de Entrada
# ==============================================================================

if __name__ == "__main__":
    executar_smartnote()
