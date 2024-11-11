from flask import Flask, render_template, request, jsonify
import pyodbc
import os
from os.path import join
import subprocess


app = Flask(__name__)
dic_codigo_path = {}
# Configuração da string de conexão
DATABASE_PATH = r"./database/os_database.accdb"
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={DATABASE_PATH};'
)

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


conn = pyodbc.connect(conn_str)
@app.route('/', methods=['GET', 'POST'])
def home():
    resultados = []
    conclusao_por_numero = {}
    sem_conclusao = []
    filtros = {}  # Define filtros como um dicionário vazio para evitar erros no template
    status = ""
    possui_conclusao = []
    nao_possui_conclusao = []
    codigos_extraidos = []
    codigos_encontrados = []
    codigos_nao_encontrados = []

    cursor = conn.cursor()
    
    # Adiciona os anos (exemplo com ano atual e próximo ano)
    cursor.execute("SELECT DISTINCT ANOS FROM Procura")
    anos = [row[0] for row in cursor.fetchall()]

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
            
            # Verificar e definir o status da busca
            if resultados:
                status = "Busca realizada com sucesso!"
            else:
                status = "Nenhum resultado encontrado para os filtros aplicados."
            
            # Processar diretórios e arquivos com base nos resultados
            for resultado in resultados:
                path = resultado[-1]
                print(path)
                for root, dirs, files in os.walk(path):
                    has_conclusao = any("02 - CONCLUSÃO" in file_name for file_name in files)
                    if has_conclusao:
                        possui_conclusao.append(root)
                    else:
                        nao_possui_conclusao.append(root)
                    
                    # Extrair e armazenar códigos dos nomes dos diretórios
                    for dir_name in dirs:
                        code = extract_code(dir_name)
                        if code:
                            codigos_extraidos.append(code)
                            dic_codigo_path[code] = join(root, dir_name)
                    
                    # Extrair e armazenar códigos dos nomes dos arquivos
                    for file_name in files:
                        code = extract_code(file_name)
                        if code:
                            codigos_extraidos.append(code)
                            dic_codigo_path[code] = join(root, file_name)

                # Verificar quais códigos estão nos caminhos de diretórios com conclusão
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

    # Renderiza o template com a variável `filtros` sempre disponível
    return render_template('indexd.html', 
                           anos=anos, 
                           sites=[],  # Deixe vazio para carregar dinamicamente
                           meses=[], 
                           os_codigos=[], 
                           categorias_primarias=[], 
                           categorias_secundarias=[], 
                           resultados=resultados, 
                           conclusao_por_numero=conclusao_por_numero, 
                           sem_conclusao=sem_conclusao, 
                           filtros=filtros,  # Passa `filtros` para evitar erro
                           status=status, 
                           codigos_extraidos=codigos_extraidos, 
                           codigos_encontrados=codigos_encontrados, 
                           codigos_nao_encontrados=codigos_nao_encontrados)



@app.route('/get_sites')
def get_sites():
    ano = request.args.get('ano')
    cursor = conn.cursor()
    query = "SELECT DISTINCT SITES FROM Procura WHERE ANOS = ?"
    cursor.execute(query, (ano,))
    sites = [row[0] for row in cursor.fetchall()]
    return jsonify(sites)


@app.route('/get_meses')
def get_meses():
    site = request.args.get('site')
    cursor = conn.cursor()
    query = "SELECT DISTINCT MES FROM Procura WHERE SITES = ?"
    cursor.execute(query, (site,))
    meses = [row[0] for row in cursor.fetchall()]
    return jsonify(meses)


@app.route('/get_os')
def get_os():
    mes = request.args.get('mes')
    cursor = conn.cursor()
    query = "SELECT DISTINCT OS FROM Procura WHERE MES = ?"
    cursor.execute(query, (mes,))
    os_codigos = [row[0] for row in cursor.fetchall()]
    return jsonify(os_codigos)


@app.route('/get_categoria_primaria')
def get_categoria_primaria():
    os = request.args.get('os')
    cursor = conn.cursor()
    query = "SELECT DISTINCT CATEGORIA_PRIMARIA FROM Procura WHERE OS = ?"
    cursor.execute(query, (os,))
    categorias_primarias = [row[0] for row in cursor.fetchall()]
    return jsonify(categorias_primarias)


@app.route('/get_categoria_secundaria')
def get_categoria_secundaria():
    categoria_primaria = request.args.get('categoria_primaria')
    cursor = conn.cursor()
    query = "SELECT DISTINCT CATEGORIA_SECUNDARIA FROM Procura WHERE CATEGORIA_PRIMARIA = ?"
    cursor.execute(query, (categoria_primaria,))
    categorias_secundarias = [row[0] for row in cursor.fetchall()]
    return jsonify(categorias_secundarias)


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
