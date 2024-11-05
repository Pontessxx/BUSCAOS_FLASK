from flask import Flask, render_template, request
import pyodbc
import os
import re

app = Flask(__name__)

# Configuração da string de conexão
DATABASE_PATH = r"./database/os_database.accdb"
conn_str = (
    r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
    f'DBQ={DATABASE_PATH};'
)

@app.route('/', methods=['GET', 'POST'])
def home():
    resultados = []
    conclusao_por_numero = {}
    sem_conclusao = []
    filtros = {}
    status = ""

    try:
        # Conectando ao banco de dados
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()

            # Obter valores únicos de ANOS, SITES, MES, CÓDIGO OS, CATEGORIA PRIMÁRIA e CATEGORIA SECUNDÁRIA da tabela PROCURA
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
                    # Definir a expressão regular para o padrão ANOMESNUM
                    padrao_anomesnum = re.compile(r'[A-Z]{2,3}\d{6,}')

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
                        if os.path.exists(path):
                            for root, dirs, files in os.walk(path):
                                for dir_name in dirs:
                                    if padrao_anomesnum.match(dir_name):
                                        full_path = os.path.join(root, dir_name)
                                        arquivos = os.listdir(full_path)
                                        conclusao_count = sum(1 for file in arquivos if "02 - CONCLUSÃO" in file)
                                        if conclusao_count > 0:
                                            conclusao_por_numero[dir_name] = conclusao_count
                                        else:
                                            sem_conclusao.append(dir_name)

                except Exception as e:
                    status = f"Erro durante a busca: {str(e)}"

    except pyodbc.Error as db_error:
        status = f"Erro de conexão com o banco de dados: {str(db_error)}"

    return render_template('index.html', anos=anos, sites=sites, meses=meses, os_codigos=os_codigos, categorias_primarias=categorias_primarias, categorias_secundarias=categorias_secundarias, resultados=resultados, conclusao_por_numero=conclusao_por_numero, sem_conclusao=sem_conclusao, filtros=filtros, status=status)

if __name__ == '__main__':
    app.run(debug=True)
