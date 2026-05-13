import hashlib
import re

class WellsNeuroCore:
    def __init__(self):
        # SENSOR 3.3.1: Captura o contexto (# game/...) e o comando (translate ou old)
        self.p_bloco = re.compile(
            r'(?P<ctx># game/.*?)\n(?:#.*?\n)*\s*(?:translate\s+\w+\s+(?P<id>\w+):|(?P<is_str>old\s+))', 
            re.MULTILINE
        )

    def extrair_dna_com_id(self, conteudo_rpy):
        mapa_cirurgico = []
        for m in self.p_bloco.finditer(conteudo_rpy):
            start_pos = m.start()
            ctx = m.group('ctx')
            buffer = conteudo_rpy[m.end() : m.end() + 800]
            
            if m.group('id'): # DIÁLOGOS DE HISTÓRIA (OS 13 EPISÓDIOS)
                # NOVA LÓGICA: Aceita opcionalmente um nome de personagem antes das aspas
                # Ex: # s "Hello" ou apenas # "Hello"
                m_orig = re.search(r'#\s+(?:\w+\s+)?"(?P<orig>.*?)"', buffer, re.DOTALL)
                m_trad = re.search(r'(?P<who>\w*)\s*"(?P<trad>.*?)"(?!\n\s*#)', buffer, re.DOTALL)
                
                if m_orig and m_trad:
                    mapa_cirurgico.append({
                        'contexto': ctx, 'id_original': m.group('id'),
                        'texto_orig': m_orig.group('orig'), 'quem': m_trad.group('who'),
                        'start': start_pos, 'end': m.end() + m_trad.end(), 'tipo': 'DIA'
                    })
            
            elif m.group('is_str'): # STRINGS DE MENU
                m_s = re.search(r'"(?P<orig>.*?)"\s+new\s+"(?P<trad>.*?)"', buffer, re.DOTALL)
                if m_s:
                    orig = m_s.group('orig')
                    mapa_cirurgico.append({
                        'contexto': ctx, 'id_original': hashlib.md5(orig.encode('utf-8', errors='ignore')).hexdigest()[:12],
                        'texto_orig': orig, 'start': start_pos, 'end': m.end() + m_s.end(), 'tipo': 'STR'
                    })

        return sorted(mapa_cirurgico, key=lambda x: x['start'])
