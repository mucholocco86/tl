import codecs
import chardet

def ler_prontuario(caminho):
    """Lê o arquivo garantindo a detecção do encoding oficial do Ren'Py"""
    with open(caminho, 'rb') as f:
        raw = f.read()
        # Detecta se é UTF-8 ou se precisa do pular o BOM (\ufeff)
        result = chardet.detect(raw)
        encoding = result['encoding'] if result['encoding'] else 'utf-8'
        if encoding.lower() == 'utf-8':
            encoding = 'utf-8-sig'
            
    with codecs.open(caminho, 'r', encoding=encoding) as f:
        return f.read()

def gravar_alta(caminho, conteudo):
    """Grava o arquivo final no padrão exigido pelo motor do jogo"""
    with codecs.open(caminho, 'w', encoding='utf-8-sig') as f:
        f.write(conteudo)
