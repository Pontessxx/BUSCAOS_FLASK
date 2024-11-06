import os
from os.path import join
from rich import print
def extract_code(text):
    # Verifica se há um padrão "OS" opcional seguido de "EE" + letra + 7 dígitos em qualquer parte do texto
    parts = text.split()
    for i, part in enumerate(parts):
        if "EE" in part and len(part) >= 10:
            # Localiza o código dentro da parte
            code_candidate = part[:10]
            
            # Verifica o formato do código
            if code_candidate.startswith("EE") and code_candidate[2].isalpha() and code_candidate[3:10].isdigit():
                # Mantém o prefixo, se houver (por exemplo, "OS EEc2101001")
                prefix = " ".join(parts[:i]) if i > 0 else ""
                return f"{prefix} {code_candidate}".strip()
    return None

def normalize_path(path):
    # Substitui cada barra simples "\" por uma barra dupla "\\"
    corrected_path = path.replace("\\", "\\\\")
    return corrected_path

# Listas para armazenar resultados
possui_conclusao = []
nao_possui_conclusao = []
codigos_extraidos = []  # Lista para armazenar os códigos encontrados

# Caminho raiz (substitua pelo caminho desejado)
path = r"C:\Users\Henrique\Downloads\01 - JANEIRO"
path = normalize_path(path)

# Itera pelos diretórios e arquivos
for root, dirs, files in os.walk(path):
    # Verifica se há algum arquivo com "02 - CONCLUSÃO" no nome no diretório atual
    has_conclusao = any("02 - CONCLUSÃO" in file_name for file_name in files)
    
    # Adiciona o diretório à lista apropriada
    if has_conclusao:
        possui_conclusao.append(root)
    else:
        nao_possui_conclusao.append(root)
    
    # Extrai e armazena códigos dos nomes dos diretórios
    for dir_name in dirs:
        code = extract_code(dir_name)  # Aplica a extração no nome do diretório
        if code:
            codigos_extraidos.append(code)
    
    # Extrai e armazena códigos dos nomes dos arquivos
    for file_name in files:
        code = extract_code(file_name)  # Aplica a extração no nome do arquivo
        if code:
            codigos_extraidos.append(code)

# Exibe os diretórios e códigos encontrados
print("Diretórios com '02 - CONCLUSÃO':")
print("\n".join(possui_conclusao))

print("\nCódigos extraídos:")
print(codigos_extraidos)
