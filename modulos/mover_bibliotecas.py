import paramiko
import time
from modulos.conexao_ssh import conectar_ssh

def mover_bibliotecas(ssh_client, origem="/opt", destino="/usr/lib"):
    
    try:

        shell = ssh_client.invoke_shell()

        shell.send("su root\n")
        time.sleep(1)
        shell.send("F@RM4C1A\n")
        time.sleep(1)
        shell.send(f"mv /opt/libclisitef.so /usr/lib\n")
        time.sleep(3)
        shell.send(f"mv /opt/libclisitef64.so /usr/lib\n")
        time.sleep(3)
        shell.send(f"mv /opt/libemv64.so /usr/lib\n")
        time.sleep(3)
        shell.send(f"mv /opt/libqrencode64.so /usr/lib\n")
        time.sleep(3)

        print("[OK] Feito a movimentação das libs!\n")

        shell.send("exit\n")

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante a movimentação das bibliotecas: {e}\n")