"""Módulo principal do SmartNote"""
import sys
from PyQt5.QtWidgets import QApplication
from interface import SmartNoteApp

def executar_smartnote():
    """Inicializa a aplicação PyQt5 e exibe a janela principal"""
    app = QApplication(sys.argv)
    window = SmartNoteApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    executar_smartnote()