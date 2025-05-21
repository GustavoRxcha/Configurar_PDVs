import pyodbc
import os
import subprocess
import time
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

#############################################################################################################################

def excluir_banco_pdv(ip_caixa):

    try:
        # Configuração da string de conexão
        conexao_banco = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={ip_caixa};"
            f"DATABASE=master;"
            #'Trusted_Connection=yes;'
            f"UID=sa;"  # Substitua pelo usuário correto
            f"PWD=ERPM@2017;"  # Substitua pela senha correta
        )

        print("Conectando ao banco de dados para exclusão...")
        conn = pyodbc.connect(conexao_banco, autocommit=True)  # Autocommit desativa transações
        cursor = conn.cursor()
        print("Conectado com sucesso!\n")

        print("Verificando existência do banco PDV...")
        if cursor.execute("SELECT DB_ID('PDV')").fetchone()[0]:
            print("Encerrando conexões ativas no banco PDV...\n")
            cursor.execute("ALTER DATABASE PDV SET SINGLE_USER WITH ROLLBACK IMMEDIATE")

            print("Excluindo banco PDV...")
            cursor.execute("DROP DATABASE PDV")
            print("[OK] Banco PDV excluído com sucesso.\n")
        else:
            print("[INFO] O banco PDV não existe. Nenhuma ação necessária.\n")

        # Fechamento da conexão
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[EXCEÇÃO] Erro ao excluir o banco PDV: {e}")

#############################################################################################################################

def restaurar_banco(ssh_client, ip_caixa, numero_caixa):
    
    try:

        excluir_banco_pdv(ip_caixa)

        comandos = [
            "apt-get remove --purge -y mssql-tools msodbcsql17",  # Remove pacotes antigos
            "apt-get autoremove -y",  # Remove dependências desnecessárias
            "apt-get update",  # Atualiza os repositórios
            "curl https://packages.microsoft.com/keys/microsoft.asc  | apt-key add -",  # Adiciona a chave GPG da Microsoft
            "curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list  > /etc/apt/sources.list.d/mssql-release.list",  # Adiciona o repositório do MSSQL
            "apt-get update",  # Atualiza novamente após adicionar o repositório
            "ACCEPT_EULA=Y apt-get install -y mssql-tools unixodbc-dev",  # Instala o mssql-tools
            "echo 'export PATH=\"$PATH:/opt/mssql-tools/bin\"' >> ~/.bashrc",  # Atualiza o PATH no .bashrc
            "source ~/.bashrc",  # Carrega as alterações do PATH
            f"/opt/mssql-tools/bin/sqlcmd -S {ip_caixa} -U sa -P ERPM@2017 -Q \"RESTORE DATABASE [PDV] FROM DISK = '/opt/Banco_PDV.bak' WITH REPLACE, RECOVERY, MOVE 'PDV' TO '/var/opt/mssql/data/PDV.mdf', MOVE 'PDV_log' TO '/var/opt/mssql/data/PDV_log.ldf';\"".format(ip_caixa)  # Usa o caminho completo para sqlcmd
        ]

        shell = ssh_client.invoke_shell()
        time.sleep(1)
        shell.send("su root\n")
        time.sleep(1)
        shell.send("F@RM4C1A\n")
        time.sleep(1)

        def enviar_comando(shell, comando, timeout=60):
            print(f"Executando comando: {comando}")
            shell.send(comando + "\n")

            # Inicializar variáveis
            output = ""
            start_time = time.time()

            while True:
                # Verificar se há dados disponíveis para leitura
                if shell.recv_ready():
                    try:
                        # Ler e decodificar a saída, ignorando bytes inválidos
                        chunk = shell.recv(1024).decode('utf-8', errors='ignore')
                        output += chunk
                        print(f"Saida parcial:\n{chunk}")
                    except UnicodeDecodeError as e:
                        print(f"[AVISO] Erro de decodificação ignorado: {e}")

                # Verificar se o comando foi concluído (prompt $ ou #)
                if "#" in output or "$" in output:
                    print("Comando concluído.")
                    break

                # Verificar se o tempo limite foi atingido
                if time.time() - start_time > timeout:
                    with open("output.log", "w") as f:
                        f.write(output)  # Salva a saída completa para análise
                    raise TimeoutError(f"Tempo limite de {timeout} segundos atingido para o comando: {comando}")

                # Aguardar um curto período antes de verificar novamente
                time.sleep(0.5)

            return output

        # Executar cada comando com a lógica robusta
        for comando in comandos:
            enviar_comando(shell, comando)

        ssh_client.close()
        print("Conexão SSH encerrada.\n")

        try:
            time.sleep(5)
            conexao_banco = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={ip_caixa};"
                f"DATABASE=PDV;"
                f"UID=sa;"  # Substitua pelo usuário correto
                f"PWD=ERPM@2017;"  # Substitua pela senha correta
            )
            conn = pyodbc.connect(conexao_banco, autocommit=True)  # Autocommit desativa transações
            cursor = conn.cursor()
            # Executar a stored procedure usp_restaura_banco_pdv
            print("Executando a usp_restaura_banco_pdv...")
            comando_sp = f"EXEC usp_restaura_banco_pdv 1, {numero_caixa}"
            cursor.execute(comando_sp)
            conn.commit()
            print("[OK] Stored procedure usp_restaura_banco_pdv executada com sucesso.\n")
            # Executar o comando "CTRL + T"
            script_dir = os.path.join(os.getcwd(), "modulos", "ScriptSQL")
            print("Executando comando 'CTRL + T'...")
            executar_script(cursor, os.path.join(script_dir, "ctrl_t.sql"))
            conn.commit()
            print("Comando 'CTRL + T' executado.\n")

            # Fechar conexão
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"[EXCEÇÃO] Erro durante a execução da USP_RESTAURA_BANCO_PDV: {e}\n")

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante a restauração do banco de dados: {e}\n")