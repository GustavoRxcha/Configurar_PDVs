import pyodbc
import os
from modulos.conexao_ssh import conectar_ssh

def executar_script(cursor, script_path, parametros=None):

    try:
        with open(script_path, "r") as file:
            script = file.read()
        
        # Substituir placeholders por parâmetros, se fornecidos
        if parametros:
            script = script.format(**parametros)
        
        cursor.execute(script)
        print(f"[OK] Script '{script_path}' executado com sucesso.")
    except Exception as e:
        print(f"[ERRO] Falha ao executar script '{script_path}': {e}")


def restaurar_banco(ip_caixa, numero_caixa):
    
    try:
        conexao_banco = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={ip_caixa};"
            f"DATABASE=master;"
            f"UID=sa;"  # Substitua pelo usuário correto
            f"PWD=ERPM@2017;"     # Substitua pela senha correta
        )

        print("Conectando ao banco de dados...")
        conn = pyodbc.connect(conexao_banco)
        cursor = conn.cursor()

        script_dir = os.path.join(os.getcwd(), "modulos", "ScriptSQL")

        print("Excluindo banco PDV existente...")
        cursor.execute("IF DB_ID('PDV') IS NOT NULL DROP DATABASE PDV")
        conn.commit()
        print("[OK] Banco PDV excluído com sucesso.")

        print("Restaurando backup do banco PDV...")
        comando_restore = (
            "RESTORE DATABASE PDV "
            "FROM DISK = '/opt/Banco_PDV.bak' "
            "WITH REPLACE"
        )
        cursor.execute(comando_restore)
        conn.commit()
        print("[OK] Backup do banco PDV restaurado com sucesso.")

        # 3. Executar a stored procedure usp_restaura_banco_pdv
        print("Executando a usp_restaura_banco_pdv...")
        comando_sp = f"EXEC usp_restaura_banco_pdv 0, {numero_caixa}"
        cursor.execute(comando_sp)
        conn.commit()
        print("[OK] Stored procedure usp_restaura_banco_pdv executada com sucesso.")

        # 4. Executar o comando "CTRL + T"
        print("Executando comando equivalente ao 'CTRL + T' a partir do arquivo ctrl_t.sql...")
        executar_script(cursor, os.path.join(script_dir, "ctrl_t.sql"))
        conn.commit()

        # Fechar conexão
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante a restauração do banco de dados: {e}")