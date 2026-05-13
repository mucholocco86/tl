import os
from pathlib import Path

def mapear_corredores(caminho_raiz):
    """
    Versão 3.3: Navegador de Profundidade.
    Varre todas as subpastas (bin, scripts, e1, etc.) sem exceção.
    """
    caminhos_encontrados = []
    # O os.walk garante que entraremos em TODAS as subpastas que vi no seu GitHub
    for raiz, subpastas, arquivos in os.walk(caminho_raiz):
        for arquivo in arquivos:
            if arquivo.lower().endswith(".rpy"):
                # normpath limpa as barras invertidas do Windows para evitar erros
                caminho_completo = os.path.join(raiz, arquivo)
                caminhos_encontrados.append(os.path.normpath(caminho_completo))
    
    # Ordenação alfabética rigorosa para manter a sincronia entre as doses
    return sorted(caminhos_encontrados)

def obter_base_hospital():
    """Retorna a pasta onde o .exe ou o script principal está rodando."""
    return Path(os.getcwd())
