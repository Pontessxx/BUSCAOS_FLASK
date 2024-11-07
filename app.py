from flask import Flask, render_template, request
import pyodbc
import os
from os.path import join
from rich import print
import subprocess

app = Flask(__name__)
app.secret_key = 'chavesecreta'

# Configuração da string de conexão
DATABASE_PATH = r"./database/os_database.accdb"
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={DATABASE_PATH};'
)

conn = pyodbc.connect(conn_str)
dic_codigo_path = {}

# Função para extrair códigos com prefixo opcional
def extract_code(text):
    parts = text.split()
    for i, part in enumerate(parts):
        if "EE" in part and len(part) >= 10:
            code_candidate = part[:10]
            if code_candidate.startswith("EE") and code_candidate[2].isalpha() and code_candidate[3:10].isdigit():
                prefix = " ".join(parts[:i]) if i > 0 else ""
                return f"{prefix} {code_candidate}".strip()
    return None


@app.route('/', methods=['GET', 'POST'])
def home():
    resultados = []
    conclusao_por_numero = {}
    sem_conclusao = []
    filtros = {}
    status = ""
    possui_conclusao = []
    nao_possui_conclusao = []
    codigos_extraidos = []
    codigos_encontrados = []
    codigos_nao_encontrados = []

    cursor = conn.cursor()
    # Obter valores únicos de ANOS, SITES, MES, CÓDIGO OS, CATEGORIA PRIMÁRIA e CATEGORIA SECUNDÁRIA
    cursor.execute("SELECT DISTINCT ANOS FROM PROCURA")
    anos = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT SITES FROM PROCURA")
    sites = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT MES FROM PROCURA")
    meses = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT OS FROM PROCURA")
    os_codigos = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT CATEGORIA_PRIMARIA FROM PROCURA")
    categorias_primarias = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT CATEGORIA_SECUNDARIA FROM PROCURA")
    categorias_secundarias = [row[0] for row in cursor.fetchall()]
    if request.method == 'POST':
        try:
            # Capturar os valores dos filtros do formulário
            ano_filtro = request.form.get('anos')
            site_filtro = request.form.get('sites')
            os_filtro = request.form.get('os')
            mes_filtro = request.form.get('meses')
            categoria_primaria_filtro = request.form.get('categoria_primaria')
            categoria_secundaria_filtro = request.form.get('categoria_secundaria')
            # Montar o dicionário de filtros para manter os valores selecionados
            filtros = {
                'anos': ano_filtro,
                'sites': site_filtro,
                'os': os_filtro,
                'meses': mes_filtro,
                'categoria_primaria': categoria_primaria_filtro,
                'categoria_secundaria': categoria_secundaria_filtro
            }
            # Executar a consulta SQL com os filtros
            query = """
                SELECT Procura.ANOS, Procura.SITES, Procura.OS, Procura.MES, Procura.CATEGORIA_PRIMARIA, Procura.CATEGORIA_SECUNDARIA, Procura.PATH
                FROM Procura
                WHERE Procura.ANOS = ?
                    AND Procura.SITES = ?
                    AND Procura.OS = ?
                    AND Procura.MES = ?
                    AND Procura.CATEGORIA_PRIMARIA = ?
                    AND Procura.CATEGORIA_SECUNDARIA = ?
            """
            cursor.execute(query, (ano_filtro, site_filtro, os_filtro, mes_filtro, categoria_primaria_filtro, categoria_secundaria_filtro))
            resultados = cursor.fetchall()
            if resultados:
                status = "Busca realizada com sucesso!"
            else:
                status = "Nenhum resultado encontrado para os filtros aplicados."
            # Percorrer os resultados para verificar os arquivos "02 - CONCLUSÃO"
            for resultado in resultados:
                path = resultado[-1]
                print(path)
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
                            dic_codigo_path[code] = join(root, dir_name)  # Armazena o código e o caminho associado
                    
                    # Extrai e armazena códigos dos nomes dos arquivos
                    for file_name in files:
                        code = extract_code(file_name)  # Aplica a extração no nome do arquivo
                        if code:
                            codigos_extraidos.append(code)
                            dic_codigo_path[code] = join(root, file_name)  # Armazena o código e o caminho associado

                # Iterar sobre os códigos extraídos e verificar se estão nos caminhos
                for codigo in codigos_extraidos:
                    encontrado = False
                    for caminho in possui_conclusao:
                        if codigo in caminho:
                            codigos_encontrados.append(codigo)
                            encontrado = True
                            break
                    if not encontrado:
                        codigos_nao_encontrados.append(codigo)

        except Exception as e:
            status = f"Erro durante a busca: {str(e)}"

    return render_template('index.html', 
                           anos=anos, 
                           sites=sites, 
                           meses=meses, 
                           os_codigos=os_codigos, 
                           categorias_primarias=categorias_primarias, 
                           categorias_secundarias=categorias_secundarias, 
                           resultados=resultados, 
                           conclusao_por_numero=conclusao_por_numero, 
                           sem_conclusao=sem_conclusao, 
                           filtros=filtros, 
                           status=status, 
                           codigos_extraidos=codigos_extraidos, 
                           codigos_encontrados=codigos_encontrados, 
                           codigos_nao_encontrados=codigos_nao_encontrados)


@app.route('/abrir_diretorio/<codigo>')
def abrir_diretorio(codigo):
    path = dic_codigo_path.get(codigo)
    if path:
        try:
            # Abra o explorador de arquivos no caminho especificado
            subprocess.Popen(f'explorer "{path}"')  # Para Windows
            # Para MacOS, use: subprocess.Popen(["open", path])
            # Para Linux, use: subprocess.Popen(["xdg-open", path])
            return f"Abrindo o explorador de arquivos em: {path}", 200
        except Exception as e:
            return f"Erro ao abrir o explorador: {e}", 500
    return "Caminho não encontrado para o código especificado.", 404


if __name__ == '__main__':
    app.run(debug=True)
