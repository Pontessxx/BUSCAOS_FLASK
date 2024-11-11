from flask import Flask, render_template, request, redirect,url_for,flash,jsonify
import pyodbc
import os
from os.path import join
from rich import print
import subprocess
from datetime import datetime
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
            
            # Processar diretórios e arquivos com base nos resultados
            # Este código extrai e classifica os códigos, preenchendo as listas `codigos_extraidos`, `codigos_encontrados`, etc.
            # Como implementado no código original
            for resultado in resultados:
                path = resultado[-1]
                print(path)
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


@app.route('/add', methods=['GET'])
def add():
    # Calcula o ano atual e o próximo ano
    current_year = datetime.now().year
    next_year = current_year + 1
    anos = [current_year, next_year]

    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT SITES FROM Procura")
    sites = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT OS FROM Procura")
    os_codigos = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT MES FROM Procura")
    meses = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT CATEGORIA_PRIMARIA FROM Procura")
    categorias_primarias = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT CATEGORIA_SECUNDARIA FROM Procura")
    categorias_secundarias = [row[0] for row in cursor.fetchall()]

    return render_template('add_record.html', anos=anos, sites=sites, os_codigos=os_codigos, 
                           meses=meses, categorias_primarias=categorias_primarias, 
                           categorias_secundarias=categorias_secundarias)

# Rota para processar o formulário e adicionar o registro ao banco de dados
@app.route('/add_record', methods=['POST'])
def add_record():
    if request.method == 'POST':
        # Obter dados do formulário
        ano = request.form.get('anos')
        site = request.form.get('sites')
        codigo_os = request.form.get('os')
        mes = request.form.get('mes')
        categoria_primaria = request.form.get('categoria_primaria')
        categoria_secundaria = request.form.get('categoria_secundaria')
        path = request.form.get('path')
        
        try:
            # Inserir dados no banco de dados, com erro_path definido como False
            cursor = conn.cursor()
            query = """
                INSERT INTO Procura (ANOS, SITES, OS, MES, CATEGORIA_PRIMARIA, CATEGORIA_SECUNDARIA, PATH, PATH_erro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (ano, site, codigo_os, mes, categoria_primaria, categoria_secundaria, path, False))
            conn.commit()
            flash("Registro adicionado com sucesso!", "success")
        except Exception as e:
            return(f"Erro ao adicionar o registro: {str(e)}", "error")
        return redirect(url_for('add'))


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
