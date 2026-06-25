import sys
import os
import speech_recognition as sr
import pyttsx3
import threading
from PySide6.QtCore import QThread, Signal, QUrl, Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QPushButton, QLineEdit, QTabWidget)
from PySide6.QtWebEngineWidgets import QWebEngineView

# --- COMANDOS POLIGLOTAS COMPLETOS ---
COMANDOS = {
    "abrir": ["ir para", "vá para", "abrir", "go to", "open", "ir a"],
    "pesquisar": ["pesquisar", "search", "buscar"],
    "nova_aba": ["nova aba", "new tab", "nueva pestaña"],
    "maximizar": ["maximizar", "maximize", "maximizar"],
    "minimizar": ["minimizar", "minimize", "minimizar"],
    "restaurar": ["restaurar", "restore", "restaurar"],
    "voltar": ["voltar", "back", "atrás", "volver"],
    "avancar": ["avançar", "forward", "adelante"],
    "atualizar": ["atualizar", "reload", "actualizar"],
    "fechar_aba": ["fechar aba", "close tab", "cerrar pestaña"],
    "fechar": ["fechar", "close", "cerrar"]
}

class VoiceThread(QThread):
    comando_recebido = Signal(str)
    def __init__(self):
        super().__init__()
        self._is_running = True
    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            while self._is_running:
                try:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)
                    comando = recognizer.recognize_google(audio, language="pt-BR,en-US,es-ES").lower()
                    self.comando_recebido.emit(comando)
                except: continue
    def stop(self):
        self._is_running = False; self.wait()

class NebulaTeen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NebulaTeen 9.1 - Global")
        self.resize(1000, 700)
        self.setStyleSheet("QMainWindow { background-color: #0d0d0d; }")
        self.init_ui()
        self.voice_thread = VoiceThread()
        self.voice_thread.comando_recebido.connect(self.processar_comando)
        self.voice_thread.start()

    def init_ui(self):
        self.container = QWidget(); self.setCentralWidget(self.container)
        self.layout_principal = QVBoxLayout(self.container)
        self.navbar = QHBoxLayout()
        
        # Controles | Barra de Endereço | Utilitários
        for txt in ["⬅", "➡", "🔄", "❌", "🏠"]: self.navbar.addWidget(QPushButton(txt))
        self.url_bar = QLineEdit(); self.navbar.addWidget(self.url_bar)
        for txt in ["📥", "🛡️", "⭐", "🕒"]: self.navbar.addWidget(QPushButton(txt))
            
        self.tabs = QTabWidget(); self.layout_principal.addLayout(self.navbar); self.layout_principal.addWidget(self.tabs)
        self.add_new_tab()

    def add_new_tab(self):
        browser = QWebEngineView(); browser.setUrl(QUrl("https://www.google.com"))
        self.tabs.addTab(browser, "Nova Aba")

    def processar_comando(self, t):
        # Comandos de Janela e Navegação
        if any(c in t for c in COMANDOS["maximizar"]): self.showMaximized()
        elif any(c in t for c in COMANDOS["minimizar"]): self.showMinimized()
        elif any(c in t for c in COMANDOS["restaurar"]): self.showNormal()
        elif any(c in t for c in COMANDOS["fechar_aba"]): self.tabs.removeTab(self.tabs.currentIndex())
        elif any(c in t for c in COMANDOS["fechar"]): self.close()
        elif any(c in t for c in COMANDOS["voltar"]): self.tabs.currentWidget().back()
        elif any(c in t for c in COMANDOS["avancar"]): self.tabs.currentWidget().forward()
        elif any(c in t for c in COMANDOS["atualizar"]): self.tabs.currentWidget().reload()
        
        # Comando Abrir (Corrigido e Seguro)
        elif any(c in t for c in COMANDOS["abrir"]):
            site = t
            for cmd in COMANDOS["abrir"]: 
                site = site.replace(cmd, "")
            site = site.strip().replace(" ", "")
            if site:
                url = f"https://www.{site}.com" if "." not in site else f"https://{site}"
                self.tabs.currentWidget().setUrl(QUrl(url))
        
        # Comando Pesquisar
        elif any(c in t for c in COMANDOS["pesquisar"]):
            termo = t
            for cmd in COMANDOS["pesquisar"]: termo = termo.replace(cmd, "")
            self.tabs.currentWidget().setUrl(QUrl(f"https://www.google.com/search?q={termo.strip()}"))

    def closeEvent(self, event):
        self.voice_thread.stop(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NebulaTeen()
    window.show()
    sys.exit(app.exec())
