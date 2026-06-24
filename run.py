import sys
import json
import os
import speech_recognition as sr
import pyttsx3
import threading
from PySide6.QtCore import QThread, Signal, QUrl, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QLabel, QPushButton, QLineEdit, QMenu, 
                               QStatusBar, QTabWidget)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile

# --- CONFIGURAÇÕES DE DIRETÓRIOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

HISTORICO_FILE = os.path.join(DATA_DIR, 'historico.json')
FAVORITOS_FILE = os.path.join(DATA_DIR, 'favoritos.json')

def carregar_dados(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            try: return json.load(f)
            except: return []
    return []

# --- TEMAS ---
TEMAS = {
    "padrao": {"style": "QMainWindow { background-color: #f0f0f0; } QPushButton { background-color: #ddd; border-radius: 10px; padding: 5px; } QLineEdit { border-radius: 10px; padding: 5px; border: 1px solid #ccc; }", "url": "https://www.google.com"},
    "batman": {"style": "QMainWindow { background-color: #2c3e50; } QLabel { color: #f1c40f; } QPushButton { background-color: #34495e; color: #f1c40f; border: 2px solid #f1c40f; border-radius: 10px; padding: 5px; } QLineEdit { border-radius: 10px; padding: 5px; background: #34495e; color: white; }", "url": "https://www.dccomics.com"},
    "dragon ball": {"style": "QMainWindow { background-color: #d35400; } QLabel { color: #f1c40f; } QPushButton { background-color: #e67e22; color: white; border-radius: 10px; padding: 5px; } QLineEdit { border-radius: 10px; padding: 5px; background: #e67e22; color: white; }", "url": "https://dragonball.com"},
    "mortal kombat": {"style": "QMainWindow { background-color: #000; } QLabel { color: #c0392b; } QPushButton { background-color: #c0392b; color: #f1c40f; border-radius: 10px; padding: 5px; } QLineEdit { border-radius: 10px; padding: 5px; background: #c0392b; color: white; }", "url": "https://www.mortalkombat.com"},
    "x-men": {"style": "QMainWindow { background-color: #2980b9; } QLabel { color: #f1c40f; } QPushButton { background-color: #2c3e50; color: #f1c40f; border-radius: 10px; padding: 5px; } QLineEdit { border-radius: 10px; padding: 5px; background: #2c3e50; color: white; }", "url": "https://www.marvel.com"},
    "sailor moon": {"style": "QMainWindow { background-color: #f1948a; } QLabel { color: #fff; } QPushButton { background-color: #a569bd; color: white; border-radius: 10px; padding: 5px; } QLineEdit { border-radius: 10px; padding: 5px; background: #a569bd; color: white; }", "url": "https://sailormoon-official.com"}
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
                    if self._is_running:
                        comando = recognizer.recognize_google(audio, language="pt-BR").lower()
                        self.comando_recebido.emit(comando)
                except Exception: continue
    def stop(self):
        self._is_running = False; self.wait()

class NebulaTeen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NebulaTeen 9.1")
        self.resize(1000, 700)
        self.tema_config = TEMAS["padrao"]
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)
        self.init_ui()
        
        self.voice_thread = VoiceThread()
        self.voice_thread.comando_recebido.connect(self.processar_comando)
        self.voice_thread.start()

    def falar(self, texto):
        def _executar_fala():
            self.engine.say(texto)
            self.engine.runAndWait()
        threading.Thread(target=_executar_fala, daemon=True).start()

    def init_ui(self):
        self.container = QWidget()
        self.layout_principal = QVBoxLayout()
        self.label_status = QLabel("NebulaTeen 9.1\n\nDiga 'vamos navegar' para iniciar...")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setFont(QFont("Arial", 16, QFont.Bold))
        self.layout_principal.addWidget(self.label_status)
        
        self.widget_navegador = QWidget()
        self.layout_navegador = QVBoxLayout()
        self.navbar = QHBoxLayout()
        
        btns = [
            ("⬅", lambda: self.current_browser().back()), ("➡", lambda: self.current_browser().forward()), 
            ("🔄", lambda: self.current_browser().reload()), ("❌", lambda: self.current_browser().stop()),
            ("🏠", lambda: self.current_browser().setUrl(QUrl(self.tema_config["url"]))),
            ("➕", self.add_new_tab)
        ]
        for txt, action in btns:
            btn = QPushButton(txt); btn.clicked.connect(action); self.navbar.addWidget(btn)
        
        self.url_bar = QLineEdit(); self.url_bar.returnPressed.connect(self.navegar_url)
        self.navbar.addWidget(self.url_bar)
        
        self.btn_down = QPushButton("📥"); self.btn_down.clicked.connect(self.abrir_pasta_downloads); self.navbar.addWidget(self.btn_down)
        self.btn_priv = QPushButton("🛡️"); self.btn_priv.clicked.connect(self.limpar_privacidade); self.navbar.addWidget(self.btn_priv)
        self.btn_fav = QPushButton("⭐"); self.btn_fav.clicked.connect(lambda: self.abrir_menu(FAVORITOS_FILE, "Favoritos", self.btn_fav)); self.navbar.addWidget(self.btn_fav)
        self.btn_hist = QPushButton("🕒"); self.btn_hist.clicked.connect(lambda: self.abrir_menu(HISTORICO_FILE, "Histórico", self.btn_hist)); self.navbar.addWidget(self.btn_hist)
        
        self.btn_tema = QPushButton("🎨"); self.menu_tema = QMenu(self)
        for t in TEMAS.keys():
            action = self.menu_tema.addAction(t.replace("-", " ").title())
            action.triggered.connect(lambda checked, t=t: self.aplicar_tema(t))
        self.btn_tema.setMenu(self.menu_tema); self.navbar.addWidget(self.btn_tema)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda i: self.tabs.removeTab(i))
        
        self.layout_navegador.addLayout(self.navbar); self.layout_navegador.addWidget(self.tabs)
        self.widget_navegador.setLayout(self.layout_navegador); self.widget_navegador.setVisible(False)
        self.layout_principal.addWidget(self.widget_navegador)
        self.setCentralWidget(self.container); self.container.setLayout(self.layout_principal)
        self.setStatusBar(QStatusBar(self))

    def current_browser(self):
        return self.tabs.currentWidget()

    def add_new_tab(self):
        browser = QWebEngineView()
        browser.setUrl(QUrl(self.tema_config["url"]))
        self.tabs.addTab(browser, "Nova Aba")
        self.tabs.setCurrentWidget(browser)
        self.widget_navegador.setVisible(True)
        self.label_status.setVisible(False)

    def navegar_url(self):
        entrada = self.url_bar.text().strip()
        if not entrada: return
        
        extensoes = [".com", ".com.br", ".br", ".net", ".org", ".edu", ".gov", ".io"]
        e_site = any(ext in entrada.lower() for ext in extensoes) or "www." in entrada.lower()

        if e_site:
            url = "https://" + entrada if not entrada.startswith("http") else entrada
        else:
            url = f"https://www.google.com/search?q={entrada}"
            
        self.current_browser().setUrl(QUrl(url))

    def aplicar_tema(self, nome_tema):
        self.tema_config = TEMAS.get(nome_tema, TEMAS["padrao"])
        self.setStyleSheet(self.tema_config["style"])
        self.label_status.setVisible(False); self.widget_navegador.setVisible(True)
        if self.tabs.count() == 0: self.add_new_tab()
        self.current_browser().setUrl(QUrl(self.tema_config["url"]))
        self.falar(f"Tema {nome_tema} ativo.")

    def limpar_privacidade(self):
        profile = QWebEngineProfile.defaultProfile()
        profile.clearHttpCache(); profile.cookieStore().deleteAllCookies()
        self.statusBar().showMessage("Privacidade limpa!", 3000); self.falar("Privacidade limpa.")

    def abrir_pasta_downloads(self): os.startfile(os.path.expanduser("~"))

    def abrir_menu(self, arquivo, titulo, btn_origem):
        menu = QMenu(self)
        for url in carregar_dados(arquivo):
            menu.addAction(url[:30] + "...").triggered.connect(lambda checked, u=url: self.current_browser().setUrl(QUrl(u)))
        menu.exec(btn_origem.mapToGlobal(btn_origem.rect().bottomLeft()))

    def processar_comando(self, texto):
        if any(trigger in texto for trigger in ["ir para", "vá para", "abrir", "www"]):
            site = texto
            for trigger in ["ir para", "vá para", "abrir", "o site", "o ", "a "]:
                site = site.replace(trigger, "")
            site = site.strip().replace(" ", "")
            if site:
                if not site.startswith("http"):
                    if "." not in site: site = f"https://www.{site}.com"
                    else: site = f"https://{site}"
                self.current_browser().setUrl(QUrl(site))
                self.falar(f"Abrindo {site}")
        elif "pesquisar" in texto:
            termo = texto.replace("pesquisar", "").strip()
            self.current_browser().setUrl(QUrl(f"https://www.google.com/search?q={termo}"))
            self.falar(f"Pesquisando por {termo}")
        elif "nova aba" in texto: self.add_new_tab(); self.falar("Abrindo nova aba")
        elif "maximizar" in texto: self.showMaximized(); self.falar("Janela maximizada")
        elif "minimizar" in texto: self.showMinimized(); self.falar("Minimizando")
        elif "restaurar" in texto: self.showNormal(); self.falar("Janela restaurada")
        elif "voltar" in texto: self.current_browser().back(); self.falar("Voltando")
        elif "avançar" in texto: self.current_browser().forward(); self.falar("Avançando")
        elif "atualizar" in texto: self.current_browser().reload(); self.falar("Atualizando")
        elif "vamos" in texto and "navegar" in texto: self.add_new_tab(); self.falar("Navegando")
        elif "fechar aba" in texto:
            index = self.tabs.currentIndex()
            if index != -1:
                self.tabs.removeTab(index)
                self.falar("Aba fechada")
        elif "fechar" in texto: self.widget_navegador.setVisible(False); self.label_status.setVisible(True); self.falar("Navegador fechado")

    def closeEvent(self, event):
        self.voice_thread.stop(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NebulaTeen()
    window.show()
    sys.exit(app.exec())
