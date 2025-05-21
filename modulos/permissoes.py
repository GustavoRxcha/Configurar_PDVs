import paramiko
from modulos.conexao_ssh import conectar_ssh
import os
from dotenv import load_dotenv
import time

load_dotenv()
SSH_USER = os.getenv("SSH_USER")
SSH_PASS = os.getenv("SSH_PASS")

def configurar_permissoes(ssh_client):
    
    try:

        shell = ssh_client.invoke_shell()

        shell.send("su root\n")
        time.sleep(1)
        shell.send("F@RM4C1A\n")
        time.sleep(1)
        shell.send("chown -R prevenda.prevenda /opt\n")
        time.sleep(4)
        shell.send("chmod -R 777 /opt\n")
        time.sleep(4)

        print("[OK] Executado comandos para dar permissão à pasta /opt\n")


        shell.send("exit\n")
    
    except Exception as e:
        print(f"[ERRO] Falha ao configurar permissões: {e}\n")
        return False
