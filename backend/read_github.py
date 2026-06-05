import urllib.request

url = "https://raw.githubusercontent.com/matheussouza17/portal-b2b-database/main/scripts/05-alter_tables_demanda.sql"
try:
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
        print("CONTEUDO COMPLETO DO ARQUIVO:")
        print(content)
except Exception as e:
    print(f"Erro ao ler URL: {e}")
