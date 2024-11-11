import os
from os.path import join
import re
from rich import *

conclusao_por_numero = {}
sem_conclusao = []
possui_conclusao = []
nao_possui_conclusao = []
codigos_extraidos = []
codigos_encontrados = []
codigos_nao_encontrados = []
dic_codigo_path = {}

def extract_code(text):
    parts = text.split()
    for i, part in enumerate(parts):
        if "EE" in part and len(part) >= 10:
            code_candidate = part[:10]
            if code_candidate.startswith("EE") and code_candidate[2].isalpha() and code_candidate[3:10].isdigit():
                prefix = " ".join(parts[:i]) if i > 0 else ""
                return f"{prefix} {code_candidate}".strip()
    return None

# Input do mês no formato "01 - JANEIRO"
input_month = "01 - JANEIRO"
month_number = input_month.split(" - ")[0]

path = r""

for root, dirs, files in os.walk(path):
    has_conclusao = any("02 - CONCLUSÃO" in file_name for file_name in files)
    if has_conclusao:
        possui_conclusao.append(root)
    else:
        nao_possui_conclusao.append(root)
    for dir_name in dirs:
        code = extract_code(dir_name)
        if code:
            codigos_extraidos.append(code)
            dic_codigo_path[code] = join(root, dir_name)
    for file_name in files:
        code = extract_code(file_name)
        if code:
            codigos_extraidos.append(code)
            dic_codigo_path[code] = join(root, file_name)

# print(codigos_extraidos)
# Ordenar os códigos extraídos
# codigos_extraidos.sort()

for codigo in codigos_extraidos:
    encontrado = False
    for caminho in possui_conclusao:
        if codigo in caminho:
            codigos_encontrados.append(codigo)
            encontrado = True
            break
    if not encontrado:
        codigos_nao_encontrados.append(codigo)


print(possui_conclusao)

print("Códigos extraídos:", codigos_extraidos)
print("Códigos encontrados:", codigos_encontrados)
print("Códigos não encontrados:", codigos_nao_encontrados)