import sys, os, time, gc, random

# --- BLOCO 1: MARCAPASSO DE BOOT ---
# Tenta carregar as bibliotecas de forma isolada para não sufocar o Celeron
try:
    import requests
    from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                                 QWidget, QFileDialog, QLabel, QProgressBar, QTextEdit, QMessageBox)
    from PySide6.QtCore import Qt, QThread, Signal
    from deep_translator import GoogleTranslator
except Exception as e:
    with open("ERRO_ESTRUTURAL_BOOT.txt", "w", encoding="utf-8") as f:
        f.write(f"Falha de hardware/biblioteca: {str(e)}")
    sys.exit(1)

# --- BLOCO 2: MOTOR DE TRADUÇÃO COM PROXY ROTATIVO ---
class TranslationWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal()

    def __init__(self, arquivos, idioma_destino):
        super().__init__()
        self.arquivos = arquivos
        self.idioma = idioma_destino
        self.proxies = []

    def buscar_entregadores(self):
        """Busca proxies para evitar bloqueio do Google."""
        self.status.emit("🕵️ Recrutando entregadores (proxies)...")
        try:
            # Busca proxies HTTP simples para maior velocidade
            url = "https://proxyscrape.com"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                self.proxies = response.text.strip().split('\r\n')
                self.status.emit(f"✅ {len(self.proxies)} identidades prontas.")
            else:
                self.status.emit("⚠️ Servidor de proxies ocupado. Usando conexão padrão.")
        except:
            self.status.emit("⚠️ Falha na rede. Iniciando sem identidades extras.")

    def run(self):
        self.buscar_entregadores()
        
        for caminho in self.arquivos:
            nome_arq = os.path.basename(caminho)
            self.status.emit(f"🚀 Operando: {nome_arq}")
            
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    linhas = f.readlines()
            except: continue

            traduzidas = []
            buffer_origem = []
            buffer_indices = []
            total = len(linhas)
            
            for i, linha in enumerate(linhas):
                traduzidas.append(linha)
                if "TRADUCAO: " in linha:
                    origem = linha.split("TRADUCAO: ", 1)[-1].strip()
                    if origem:
                        buffer_origem.append(origem)
                        buffer_indices.append(i)

                # DISPARO COM ROTAÇÃO (Lotes de 30 a 45 para não travar o Celeron)
                if len(buffer_origem) >= random.randint(30, 45) or (i == total - 1 and buffer_origem):
                    sucesso = False
                    tentativas = 0
                    while not sucesso and tentativas < 3:
                        try:
                            # Seleciona um rosto diferente (Proxy)
                            p = random.choice(self.proxies) if self.proxies else None
                            p_dict = {"http": f"http://{p}", "https": f"http://{p}"} if p else None
                            
                            trans = GoogleTranslator(source='en', target=self.idioma, proxies=p_dict)
                            
                            # Simulação de humano: pausa randômica
                            time.sleep(random.uniform(1.5, 3.0))
                            
                            lote = trans.translate_iterable(buffer_origem)
                            for idx, texto in enumerate(lote):
                                traduzidas[buffer_indices[idx]] = f"TRADUCAO: {texto}\n"
                            
                            sucesso = True
                            buffer_origem = []; buffer_indices = []
                        except:
                            tentativas += 1
                            if p in self.proxies: self.proxies.remove(p)
                            time.sleep(1)

                if i % 100 == 0:
                    self.progress.emit(int((i / total) * 100))
                    QApplication.processEvents()

            # Salva o arquivo e libera a RAM
            saida = os.path.join(os.path.dirname(caminho), f"TRADUZIDO_{nome_arq}")
            with open(saida, 'w', encoding='utf-8') as f:
                f.write("".join(traduzidas))
            gc.collect()

        self.finished.emit()

# --- BLOCO 3: INTERFACE VISUAL ---
class WellsTranslatorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wells Translator Satellite v2.2.1 - Stability Mode")
        self.setMinimumSize(750, 550)
        self.arquivos_selecionados = []

        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.monitor = QLabel("ESTABILIDADE v2.2.1 ATIVA\nFocado em Hardware de Baixo Consumo")
        self.monitor.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ffcc; background: #0a0a0a; padding: 25px; border-radius: 12px; border: 2px solid #00ffcc;")
        self.monitor.setAlignment(Qt.AlignCenter); self.layout.addWidget(self.monitor)

        self.progresso = QProgressBar(); self.progresso.setFixedHeight(30); self.layout.addWidget(self.progresso)
        
        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.log.setStyleSheet("background: #000; color: #00ff00; font-family: Consolas;"); self.layout.addWidget(self.log)

        self.btn_select = QPushButton("1. SELECIONAR DOSES (.txt)"); self.btn_select.setMinimumHeight(60)
        self.btn_select.clicked.connect(self.selecionar); self.layout.addWidget(self.btn_select)

        self.btn_start = QPushButton("2. INICIAR TRADUÇÃO"); self.btn_start.setMinimumHeight(60)
        self.btn_start.setEnabled(False); self.btn_start.clicked.connect(self.iniciar); self.layout.addWidget(self.btn_start)

    def selecionar(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Doses do Hospital", "", "TXT (*.txt)")
        if files:
            self.arquivos_selecionados = files
            self.monitor.setText(f"{len(files)} doses carregadas.")
            self.btn_start.setEnabled(True)

    def iniciar(self):
        self.btn_select.setEnabled(False); self.btn_start.setEnabled(False)
        self.worker = TranslationWorker(self.arquivos_selecionados, 'pt')
        self.worker.progress.connect(self.progresso.setValue)
        self.worker.status.connect(lambda s: self.log.append(s))
        self.worker.finished.connect(self.finalizado)
        self.worker.start()

    def finalizado(self):
        QMessageBox.information(self, "Sucesso", "Tradução concluída!")
        self.btn_select.setEnabled(True); self.btn_start.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion"); h = WellsTranslatorUI(); h.show(); sys.exit(app.exec())
