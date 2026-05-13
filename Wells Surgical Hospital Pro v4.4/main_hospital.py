import sys, os, time, gc, re
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QWidget, QFileDialog, QLabel, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt

# Motores de Elite v4.6
import util
import codegen
import translate
import wells_path_utils
import wells_encoding_handler
from wells_pharmacist import WellsPharmacist

try:
    from docx import Document
except ImportError:
    pass

class WellsHospitalV46(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wells Surgical Hospital Pro v4.6 - DNA Sync")
        self.setMinimumSize(850, 700)
        
        self.farmacia = WellsPharmacist()
        self.pacientes = []
        self.fase = 0 

        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.monitor = QLabel("ESTRUTURA DE INJEÇÃO v4.6\nSincronia por DNA Digital (MD5)")
        self.monitor.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ffcc; background: #0a0a0a; padding: 25px; border-radius: 12px; border: 2px solid #00ffcc;")
        self.monitor.setAlignment(Qt.AlignCenter); self.layout.addWidget(self.monitor)
        
        self.progresso = QProgressBar(); self.progresso.setFixedHeight(30); self.layout.addWidget(self.progresso)
        self.btn_acao = QPushButton("1. TRIAGEM E GERAR DOSES DOCX"); self.btn_acao.setMinimumHeight(130)
        self.btn_acao.setStyleSheet("QPushButton { background-color: #1a1a2e; color: #00ffcc; border-radius: 15px; font-size: 24px; font-weight: bold; border: 3px solid #0f3460; }")
        self.btn_acao.clicked.connect(self.gerenciar_hospital); self.layout.addWidget(self.btn_acao)

    def gerenciar_hospital(self):
        if self.fase == 0: self.fluxo_triagem()
        else: self.fluxo_cirurgia()

    def fluxo_triagem(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecionar Pasta /tl", "")
        if not pasta: return
        arqs = sorted(wells_path_utils.mapear_corredores(pasta))
        self.pacientes = []; textos_gabarito = []

        for i, caminho in enumerate(arqs):
            try:
                time.sleep(0.12)
                conteudo = wells_encoding_handler.ler_prontuario(caminho)
                from wells_neuro_core import WellsNeuroCore
                neuro = WellsNeuroCore()
                mapa = neuro.extrair_dna_com_id(conteudo)
                if mapa:
                    self.pacientes.append({'caminho': caminho, 'mapa': mapa, 'conteudo': conteudo})
                    for item in mapa:
                        bloco = f"{item['contexto']}\nID: {item['id_original']}\nORIGEM: {item['texto_orig']}\nTRADUÇÃO: {item['texto_orig']}"
                        textos_gabarito.append(bloco)
                if i % 5 == 0: gc.collect()
                self.monitor.setText(f"MAPEANDO ({i+1}/{len(arqs)})\n{os.path.basename(caminho)}")
                self.progresso.setValue(int((i+1)/len(arqs)*100))
                QApplication.processEvents()
            except: pass

        if textos_gabarito:
            self.farmacia.preparar_doses(textos_gabarito)
            self.fase = 1
            self.btn_acao.setText("2. INJETAR TRADUÇÕES (DOCX)"); self.btn_acao.setStyleSheet("background-color: #4a1a2e; color: #ff0044; border-radius: 15px;")
            os.startfile(os.getcwd())

    def fluxo_cirurgia(self):
        dicionario_global = {}
        doses_docx = sorted(list(Path(os.getcwd()).glob("GABARITO_DOSE_*.docx")))
        
        if not doses_docx:
            QMessageBox.critical(self, "Erro", "Nenhuma dose GABARITO_DOSE_*.docx encontrada!"); return

        for dose_path in doses_docx:
            self.monitor.setText(f"LENDO DOSE: {dose_path.name}")
            try:
                doc = Document(dose_path)
                # Captura todo o texto do documento para análise de DNA
                texto_completo = "\n".join([p.text for p in doc.paragraphs])
                
                # Fatiamos o documento onde quer que o Google tenha escrito ID ou IDENTIFICAÇÃO
                blocos_id = re.split(r'(?:ID|Identificação|Identificacao|id):\s*', texto_completo, flags=re.IGNORECASE)
                
                for bloco in blocos_id:
                    # Busca o DNA (MD5 de 32 chars ou epX_)
                    m_id = re.search(r'([a-f0-9]{32}|ep\d+_[a-f0-9]+)', bloco)
                    if m_id:
                        id_encontrado = m_id.group(1).strip()
                        
                        # A tradução está SEMPRE após a etiqueta de tradução (independente de acento)
                        partes = re.split(r'(?:TRADUCAO|TRADUÇÃO|TRADUÇAO|Traducao|Tradução):\s*', bloco, flags=re.IGNORECASE)
                        if len(partes) > 1:
                            # Pegamos a última parte do bloco (o texto em português)
                            texto_traduzido = partes[-1].strip()
                            if texto_traduzido:
                                dicionario_global[id_encontrado] = texto_traduzido
                
                gc.collect(); QApplication.processEvents()
            except Exception as e:
                print(f"Erro na dose {dose_path.name}: {e}")

        # VERIFICAÇÃO DE SUCESSO DO BANCO DE DADOS
        if not dicionario_global:
            self.monitor.setText("ERRO: DICIONÁRIO VAZIO")
            QMessageBox.critical(self, "Erro de Sincronia", "O Hospital não conseguiu parear os IDs no Word. Verifique os nomes dos arquivos."); return

        self.monitor.setText(f"BANCO DE DADOS: {len(dicionario_global)} FRASES")
        
        # INJEÇÃO REAL NOS ARQUIVOS .RPY
        for i, p in enumerate(self.pacientes):
            self.monitor.setText(f"INJETANDO ({i+1}/{len(self.pacientes)})\n{os.path.basename(p['caminho'])}")
            from wells_surgeon import WellsSurgeon
            cirurgiao = WellsSurgeon()
            cirurgiao.realizar_transplante_id(p['caminho'], p['mapa'], dicionario_global)
            
            time.sleep(0.05); gc.collect(); QApplication.processEvents()
            self.progresso.setValue(int((i+1)/len(self.pacientes)*100))

        self.monitor.setText("ALTA CONCEDIDA!"); self.fase = 0
        QMessageBox.information(self, "Wells v4.6", f"Sucesso Industrial! {len(dicionario_global)} frases injetadas.")

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion"); h = WellsHospitalV46(); h.show(); sys.exit(app.exec())
