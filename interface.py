"""Módulo de interface gráfica (UI) para o SmartNote."""
import requests
import spacy
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTextEdit, QLabel, QLineEdit, QListWidget, QWidget,
    QMessageBox, QDialog, QScrollArea, QSlider, QInputDialog, QFrame
)
from PyQt5.QtGui import QTextCursor
from sentence_transformers import SentenceTransformer

import notas_processor
import infra_texto

class ConfiguraçõesAvancadasDialog(QDialog):
    """Janela de diálogo para configurações avançadas de threshold e stopwords."""
    def __init__(self, parent=None):
        """Inicializa a janela de diálogo de configurações com sliders e listas."""
        super().__init__(parent)
        self.setWindowTitle("Configurações Avançadas")
        self.setGeometry(200, 200, 400, 300)
        self.layout = QVBoxLayout()
        
        stopwords_frame = QFrame()
        stopwords_frame.setFrameShape(QFrame.StyledPanel)
        stopwords_layout = QVBoxLayout(stopwords_frame)
        self.stopwords_list = QListWidget()
        self.btn_add_stopword = QPushButton("Adicionar Stopword")
        self.btn_remove_stopword = QPushButton("Remover Selecionada")
        stopwords_layout.addWidget(QLabel("Palavras Ignoradas:"))
        stopwords_layout.addWidget(self.stopwords_list)
        stopwords_layout.addWidget(self.btn_add_stopword)
        stopwords_layout.addWidget(self.btn_remove_stopword)     
        self.layout.addWidget(stopwords_frame)
        self.setLayout(self.layout)

class JanelaDePreviaDeAlteracoes(QDialog):
    """Janela de pré-visualização que mostra diferenças entre texto original e modificado."""
    def __init__(self, original, modified, parent=None):
        """Inicializa a janela de pré-visualização com o conteúdo original e modificado."""
        super().__init__(parent)
        self.setWindowTitle("Pré-visualização de Alterações")
        self.setGeometry(300, 300, 800, 600)
        layout = QVBoxLayout()
        self.scroll = QScrollArea()
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        diff_html = []
        for o_line, m_line in zip(original.split('\n'), modified.split('\n')):
            if o_line != m_line:
                diff_html.append(f'<div style="background-color: #e3f2fd; border-left: 3px solid #2196F3; padding: 5px;">{m_line}</div>')
            else:
                diff_html.append(f'<div style="padding: 5px;">{m_line}</div>')
        self.content.setHtml('\n'.join(diff_html))
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)
        btn_box = QHBoxLayout()
        self.btn_confirm = QPushButton("✅ Confirmar Alterações")
        self.btn_cancel = QPushButton("❌ Cancelar")
        btn_box.addWidget(self.btn_confirm)
        btn_box.addWidget(self.btn_cancel)
        layout.addLayout(btn_box)
        self.setLayout(layout)

class SmartNoteApp(QMainWindow):
    """Janela principal da aplicação SmartNote."""

    def __init__(self):
        """Inicializa a janela principal, carregando modelos e configurando a interface."""
        super().__init__()
        self.nlp = spacy.load('pt_core_news_sm')
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.arquivos = []  
        self.title_index = None  
        self.title_embeddings = None  
        self.STOPWORDS = infra_texto.carregar_palavras_ignoradas()
        self.initUI()
        self.setWindowTitle('SmartNote')
        self.setGeometry(100, 100, 1200, 800)

    def initUI(self):
        """Configura todos os elementos da interface gráfica (menus, botões, layouts)."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)  
        toolbar_layout = QHBoxLayout()
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('Arquivo')
        file_menu.addAction('Carregar Notas', self.carregar_notas_dialog)
        file_menu.addAction('Sair', self.close)
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_button = QPushButton('🔍 Pesquisar')
        self.search_button.clicked.connect(self.buscar_palavra)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        toolbar_layout.addStretch(1)
        toolbar_layout.addLayout(search_layout)
        main_layout.addLayout(toolbar_layout)
        content_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        self.notas_list = QListWidget()
        self.notas_list.itemClicked.connect(self.exibir_conteudo_da_nota)
        left_layout.addWidget(QLabel("Notas Carregadas:"))
        left_layout.addWidget(self.notas_list)
        right_layout = QVBoxLayout()
        self.text_area = QTextEdit()
        right_layout.addWidget(QLabel("Conteúdo da Nota:"))
        right_layout.addWidget(self.text_area)
        control_layout = QHBoxLayout()
        self.process_button = QPushButton('🔗 Processar Links')
        self.process_button.clicked.connect(lambda: self.gerar_conexoes_automaticas(preview_mode=True))
        self.save_button = QPushButton('💾 Salvar Tudo')
        self.save_button.clicked.connect(self.salvar_alteracoes)
        self.settings_button = QPushButton('⚙️ Configurar')
        self.settings_button.clicked.connect(self.abrir_configuracoes)
        control_layout.addWidget(self.process_button)
        control_layout.addWidget(self.save_button)
        control_layout.addWidget(self.settings_button)
        right_layout.addLayout(control_layout)
        ia_layout = QVBoxLayout()
        self.ia_conversation_area = QTextEdit()
        self.ia_conversation_area.setReadOnly(True)
        ia_layout.addWidget(QLabel("Conversa com a IA:"))
        ia_layout.addWidget(self.ia_conversation_area)
        self.ia_input = QLineEdit()
        self.ia_button = QPushButton('🤖 Perguntar à IA')
        self.ia_button.clicked.connect(self.ask_ollama)
        ia_layout.addWidget(self.ia_input)
        ia_layout.addWidget(self.ia_button)
        right_layout.addLayout(ia_layout)
        content_layout.addLayout(left_layout, 30)
        content_layout.addLayout(right_layout, 70)
        main_layout.addLayout(content_layout)

    def buscar_palavra(self):
        """Busca uma palavra na lista de notas carregadas e destaca suas ocorrências."""
        palavra = self.search_input.text().strip().lower()
        if not palavra:
            QMessageBox.warning(self, 'Aviso', 'Por favor, insira uma palavra para buscar!')
            return
        palavra_normalizada = infra_texto.remover_acentos(palavra)
        ocorrencias = []
        for idx, arq in enumerate(self.arquivos):
            conteudo_normalizado = infra_texto.remover_acentos(arq['conteudo'].lower())
            start = 0
            while (start := conteudo_normalizado.find(palavra_normalizada, start)) != -1:
                ocorrencias.append((idx, start, arq))
                start += len(palavra_normalizada)
        if ocorrencias:
            self.mostrar_ocorrencias(ocorrencias)
        else:
            QMessageBox.information(self, 'Sem Resultados', 'Nenhuma ocorrência encontrada para a palavra fornecida.')

    def mostrar_ocorrencias(self, ocorrencias):
        """Exibe uma janela de navegação para percorrer as ocorrências encontradas."""
        self.ocorrencias_index = 0
        self.ocorrencias = ocorrencias
        self.exibir_conteudo_da_ocorrencia()
        self.criar_janela_de_navegacao()

    def criar_janela_de_navegacao(self):
        """Cria um diálogo para navegar pelas ocorrências encontradas."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ocorrências Encontradas")
        layout = QVBoxLayout()
        self.label_ocorrencia = QLabel(f'Ocorrência {self.ocorrencias_index + 1} de {len(self.ocorrencias)}')
        layout.addWidget(self.label_ocorrencia)
        self.proximo_button = QPushButton('Próximo')
        self.proximo_button.clicked.connect(self.proximo_ocorrencia)
        layout.addWidget(self.proximo_button)
        dialog.setLayout(layout)
        dialog.exec_()

    def proximo_ocorrencia(self):
        """Avança para a próxima ocorrência na lista de ocorrências encontradas."""
        if self.ocorrencias_index < len(self.ocorrencias) - 1:
            self.ocorrencias_index += 1
            self.exibir_conteudo_da_ocorrencia()
            self.label_ocorrencia.setText(f'Ocorrência {self.ocorrencias_index + 1} de {len(self.ocorrencias)}')

    def exibir_conteudo_da_ocorrencia(self):
        """Exibe o conteúdo da nota atual e destaca a ocorrência selecionada."""
        idx, start, arq = self.ocorrencias[self.ocorrencias_index]
        self.text_area.setPlainText(arq['conteudo'])
        cursor = self.text_area.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + len(self.search_input.text()), QTextCursor.KeepAnchor)
        self.text_area.setTextCursor(cursor)

    def gerar_conexoes_automaticas(self, preview_mode=True):
        """Executa o processamento de links entre notas, sugerindo links para conceitos comuns.

        Se `preview_mode` for True, mostra uma pré-visualização das alterações sem salvar diretamente.
        Caso contrário, aplica as alterações diretamente nas notas carregadas.
        """
        print("\n" + "="*50)
        print("INICIANDO PROCESSAMENTO DE LINKS")
        print("="*50)
        if not self.arquivos:
            print("⚠️ Nenhuma nota carregada. Processamento cancelado.")
            QMessageBox.warning(self, 'Aviso', 'Nenhuma nota foi carregada!')
            return
        arquivos_tmp = [arq.copy() for arq in self.arquivos]
        arquivos_atualizados = notas_processor.gerar_conexoes_automaticas(arquivos_tmp, self.nlp, self.STOPWORDS)
        if preview_mode:
            self.mostrar_preview(arquivos_atualizados)
        else:
            self.arquivos = arquivos_atualizados
            self._atualizar_lista_notas()

    def salvar_alteracoes(self):
        """Salva em disco todas as notas com suas alterações no conteúdo."""
        try:
            for arq in self.arquivos:
                with open(arq['caminho'], 'w', encoding='utf-8') as f:
                    f.write(arq['conteudo'])
            QMessageBox.information(self, 'Sucesso', 'Notas salvas com sucesso!')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao salvar: {str(e)}')

    def mostrar_preview(self, arquivos_tmp):
        """Abre a janela de pré-visualização para mostrar diferenças antes de aplicar alterações."""
        current_index = self.notas_list.currentRow()
        if current_index < 0:
            return
        preview_dialog = JanelaDePreviaDeAlteracoes(
            self.arquivos[current_index]['conteudo'],
            arquivos_tmp[current_index]['conteudo'],
            self
        )
        preview_dialog.btn_confirm.clicked.connect(lambda: (
            self._aplicar_alteracoes(arquivos_tmp),
            preview_dialog.close()
        ))
        preview_dialog.btn_cancel.clicked.connect(preview_dialog.close)
        preview_dialog.exec_()

    def _aplicar_alteracoes(self, arquivos_tmp):
        """Confirma as alterações do preview, aplicando-as às notas carregadas."""
        self.arquivos = arquivos_tmp
        self._atualizar_lista_notas()
        QMessageBox.information(self, 'Sucesso', 'Alterações aplicadas com sucesso!')

    def carregar_notas_dialog(self):
        """Abre um diálogo para selecionar a pasta de notas do Obsidian."""
        directory = QFileDialog.getExistingDirectory(self, 'Selecione a Pasta de Notas')
        if directory:
            self.carregar_notas(directory)

    def carregar_notas(self, diretorio):
        """Carrega todos os arquivos markdown (.md) de um diretório de notas."""
        self.arquivos = notas_processor.carregar_notas_de_diretorio(diretorio)
        self._atualizar_lista_notas()
        self.title_index, self.title_embeddings = notas_processor.criar_indice_embeddings(
            self.model, [arq['titulo'] for arq in self.arquivos]
        )

    def _atualizar_lista_notas(self):
        """Atualiza o widget de lista de notas após carregar ou modificar notas."""
        self.notas_list.clear()
        for arquivo in self.arquivos:
            self.notas_list.addItem(arquivo['titulo'])

    def exibir_conteudo_da_nota(self):
        """Exibe o conteúdo completo da nota selecionada na interface."""
        current_row = self.notas_list.currentRow()
        if current_row >= 0:
            self.text_area.setPlainText(self.arquivos[current_row]['conteudo'])

    def abrir_configuracoes(self):
        """Abre a janela de configurações para ajustar threshold e stopwords."""
        dialog = ConfiguraçõesAvancadasDialog(self)
        dialog.stopwords_list.addItems(sorted(self.STOPWORDS))
        dialog.btn_add_stopword.clicked.connect(lambda: self.adicionar_stopword(dialog))
        dialog.btn_remove_stopword.clicked.connect(lambda: self.remover_stopword(dialog))
        if dialog.exec_():
            infra_texto.salvar_palavras_ignoradas(self.STOPWORDS)

    def adicionar_stopword(self, dialog):
        """Adiciona uma nova palavra à lista de stopwords (palavras ignoradas)."""
        text, ok = QInputDialog.getText(self, 'Nova Stopword', 'Digite a palavra:')
        if ok and text.strip():
            text = text.strip().lower()
            if text not in self.STOPWORDS:
                self.STOPWORDS.add(text)
                dialog.stopwords_list.addItem(text)
                infra_texto.salvar_palavras_ignoradas(self.STOPWORDS) 


    def remover_stopword(self, dialog):
        """Remove a stopword selecionada da lista de stopwords."""
        item = dialog.stopwords_list.currentItem()
        if item:
            self.STOPWORDS.remove(item.text())
            dialog.stopwords_list.takeItem(dialog.stopwords_list.row(item))
            infra_texto.salvar_palavras_ignoradas(self.STOPWORDS)


    def ask_ollama(self):
        """Envia a pergunta atual para o modelo de IA (Ollama) e mostra a resposta."""
        question = self.ia_input.text().strip()
        if not question:
            return
        try:
            current_note = self.arquivos[self.notas_list.currentRow()]
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma:2b",
                    "prompt": f"Contexto:\n{current_note['conteudo']}\n\nPergunta: {question}\nResposta:",
                    "stream": False,
                    "options": {"temperature": 0.5}
                },
                timeout=30
            )
            if response.status_code == 200:
                resposta = response.json().get('response', '')
                self.ia_conversation_area.append(f"[Pergunta]: {question}")
                self.ia_conversation_area.append(f"[Resposta]: {resposta}")
                self.ia_input.clear()
            else:
                QMessageBox.warning(self, 'Erro', 'Falha na comunicação com a IA')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro na consulta à IA: {str(e)}')