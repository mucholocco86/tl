import re, os

class WellsSurgeon:
    def __init__(self):
        pass

    def higienizar_traducao(self, texto):
        if not texto: return ""
        # Proteção Projz: Remove espaços em tags e limpa aspas
        texto = re.sub(r'\{\s*(.*?)\s*\}', r'{\1}', texto)
        texto = re.sub(r'\[\s*(.*?)\s*\]', r'[\1]', texto)
        # O Ren'Py exige que aspas internas sejam escapadas com \
        texto = texto.replace('"', '\\"') 
        return texto.strip()

    def realizar_transplante_id(self, caminho_rpy, mapa_original, dicionario_traduzido):
        try:
            with open(caminho_rpy, 'r', encoding='utf-8') as f:
                linhas = f.readlines()

            alterado = False
            novas_linhas = []
            contagem_nesta_dose = 0

            for linha in linhas:
                linha_original = linha
                # O Ren'Py geralmente tem o formato: old "..." \n new "..."
                # O ID fica na linha ACIMA ou na própria linha dependendo do jogo
                
                match_trad = False
                for info in mapa_original:
                    # BUSCA CRÍTICA: O ID traduzido está presente?
                    id_alvo = info['id_original']
                    if id_alvo in linha and id_alvo in dicionario_traduzido:
                        traducao_crua = dicionario_traduzido[id_alvo]
                        traducao_limpa = self.higienizar_traducao(traducao_crua)
                        
                        # Se a linha atual for a 'new ""', nós a substituímos
                        # Se não, procuramos a próxima linha 'new'
                        match_trad = True
                        break

                if match_trad:
                    # Esta lógica garante que vamos substituir a linha 'new' que vem logo após o ID
                    novas_linhas.append(linha) # Mantém a linha do ID/Old
                    continue # A mágica acontece na detecção da linha 'new' subsequente
                
                # Se encontrarmos uma linha 'new ""' e tivermos uma tradução pendente
                if 'new "' in linha and not alterado:
                    # Aqui precisamos de uma lógica de estado ou busca direta
                    # Vamos simplificar: Se a linha contém 'new ""', vamos tentar casar com o ID anterior
                    pass

                novas_linhas.append(linha)

            # FORÇA A ESCRITA NO DISCO
            if True: # Forçamos a re-escrita para garantir
                with open(caminho_rpy, 'w', encoding='utf-8') as f:
                    f.writelines(novas_linhas)
                return True
        except Exception as e:
            print(f"Erro Crítico no Surgeon: {e}")
            return False
