import paramiko
import time
from modulos.conexao_ssh import conectar_ssh

def descompactar_arquivos(ssh_client):

    try:

        shell = ssh_client.invoke_shell()

        shell.send("su root\n")
        time.sleep(1)
        shell.send("F@RM4C1A\n")
        time.sleep(1)
        shell.send("cd /opt/ && unzip -o Banco_PDV.zip\n")
        time.sleep(5)
        shell.send("cd /opt/pdv/ && unzip -o Schemas.zip\n")
        time.sleep(5)

        print("[OK] Feito a descompactação dos arquivos!\n")

        shell.send("exit\n")

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante descompactação: {e}\n")