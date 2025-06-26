#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
Projeto de Engenharia Informática - SmartNote
Autor: Daniel Gonçalves
Curso: Engenharia Informática
Data: 2025
Ficheiro: backlinks.py
Descrição: Módulo de gestão e exibição de backlinks semânticos entre notas.
===============================================================================
"""

from typing import List, Dict, Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QHBoxLayout
from PyQt5.QtCore import pyqtSignal


# ==============================================================================
# Classe de Gestão de Backlinks
# ==============================================================================

class GestorBacklinks:
    """
    Classe responsável por gerir os backlinks semânticos entre notas.
    """

    def __init__(self):
        self.backlinks = {}
        self.links_semanticos = {}

    def registrar_link_semantico(self, origem: str, destino: str, termo: str):
        """
        Registra um novo link semântico entre notas.

        Args:
            origem (str): Título da nota de origem.
            destino (str): Título da nota de destino.
            termo (str): Termo que liga semanticamente as notas.
        """
        if destino not in self.links_semanticos:
            self.links_semanticos[destino] = []
        self.links_semanticos[destino].append({
            "origem": origem,
            "termo": termo,
            "tipo": "semantico"
        })


    def obter_backlinks_para(self, titulo_nota: str) -> List[Dict]:
        """
        Obtém todos os backlinks que apontam para a nota indicada.

        Args:
            titulo_nota (str): Título da nota de destino.

        Returns:
            List[Dict]: Lista de dicionários com origem, termo e tipo.
        """
        backlinks = []

        if titulo_nota in self.links_semanticos:
            for link in self.links_semanticos[titulo_nota]:
                backlinks.append({
                    "nota_origem": link["origem"],
                    "termo": link["termo"],
                    "tipo": "semantico"
                })

        return backlinks


    def remover_backlinks_invalidos(self, titulos_validos: set):
        """
        Remove backlinks cujas notas de origem ou destino não existem mais.

        Args:
            titulos_validos (set): Conjunto de títulos válidos.
        """
        novos_backlinks = {}
        for origem, destinos in self.backlinks.items():
            if origem not in titulos_validos:
                continue

            destinos_filtrados = [d for d in destinos if d in titulos_validos]
            if destinos_filtrados:
                novos_backlinks[origem] = destinos_filtrados

        self.backlinks = novos_backlinks

# ==============================================================================
# Painel Visual de Backlinks
# ==============================================================================

class PainelBacklinks(QWidget):
    """
    Painel gráfico para exibir backlinks de uma nota.

    Sinal:
        abrir_nota_solicitada (str): Emitido quando um link é clicado.
    """

    abrir_nota_solicitada = pyqtSignal(str)

    def __init__(self, gestor_backlinks: GestorBacklinks, parent=None):
        super().__init__(parent)
        self.gestor_backlinks = gestor_backlinks
        self.initUI()

    def initUI(self):
        """Inicializa o layout principal do painel."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def atualizar_backlinks(self, nota_atual: Optional[Dict]):
        """
        Atualiza o painel com os backlinks da nota atual.

        Args:
            nota_atual (Dict): Nota em foco com campo 'titulo'.
        """
        # Limpar layout anterior
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not nota_atual:
            return

        backlinks = self.gestor_backlinks.obter_backlinks_para(nota_atual['titulo'])
        if not backlinks:
            return

        label_titulo = QLabel("Ligações Semânticas:")
        label_titulo.setStyleSheet("font-weight: bold; font-size: 11pt; margin-bottom: 10px;")
        self.layout.addWidget(label_titulo)

        # Agrupar backlinks por nota de origem
        backlinks_por_origem = {}
        for link in backlinks:
            origem = link["nota_origem"]
            backlinks_por_origem.setdefault(origem, []).append(link)

        for origem, links in backlinks_por_origem.items():
            grupo_origem = QGroupBox()
            grupo_origem.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    margin-top: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
            """)
            layout_grupo = QVBoxLayout()

            # Cabeçalho com título da nota e botão de remoção
            cabecalho = QHBoxLayout()
            label_titulo = QLabel(f"Nota: {origem}")
            label_titulo.setStyleSheet("font-weight: bold")
            btn_fechar = QPushButton("✕")
            btn_fechar.setFixedSize(16, 16)
            btn_fechar.setStyleSheet("border: none; color: red; font-weight: bold;")
            btn_fechar.clicked.connect(
                lambda _, box=grupo_origem, destino=nota_atual["titulo"], origem=origem:
                    self._remover_grupo_backlink(box, origem, destino)
            )
            cabecalho.addWidget(label_titulo)
            cabecalho.addStretch()
            cabecalho.addWidget(btn_fechar)
            layout_grupo.addLayout(cabecalho)

            # Botões para cada termo
            for link in links:
                termo_exibicao = link["termo"].replace("sem:", "").strip()
                btn_link = QPushButton(termo_exibicao)
                btn_link.setToolTip(link["termo"])
                btn_link.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        border: none;
                        color: #0645AD;
                        padding: 2px 5px;
                        font-size: 9pt;
                        max-width: 250px;
                    }
                    QPushButton:hover {
                        text-decoration: underline;
                        color: #0B0080;
                    }
                """)
                btn_link.clicked.connect(
                    lambda checked, dest=origem:
                        self.abrir_nota_solicitada.emit(dest)
                )
                layout_grupo.addWidget(btn_link)

            grupo_origem.setLayout(layout_grupo)
            self.layout.addWidget(grupo_origem)

        self.layout.addStretch()

    def _remover_grupo_backlink(self, grupo: QWidget, origem: str, destino: str):
        """
        Remove backlinks de origem para destino e atualiza o painel.

        Args:
            grupo (QWidget): Widget visual do grupo a remover.
            origem (str): Título da nota de origem.
            destino (str): Título da nota de destino.
        """
        if destino in self.gestor_backlinks.links_semanticos:
            self.gestor_backlinks.links_semanticos[destino] = [
                link for link in self.gestor_backlinks.links_semanticos[destino]
                if link["origem"] != origem
            ]
            if not self.gestor_backlinks.links_semanticos[destino]:
                del self.gestor_backlinks.links_semanticos[destino]

        grupo.setParent(None)
        grupo.deleteLater()
