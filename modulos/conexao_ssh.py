import paramiko
import os
from dotenv import load_dotenv

load_dotenv()

SSH_USER = os.getenv("SSH_USER")
SSH_PASS = os.getenv("SSH_PASS")

def conectar_ssh(ip: str):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=ip,
            username=SSH_USER,
            password=SSH_PASS
        )
        print(f"[OK] Conectado ao terminal {ip}")
        return client
    
    except Exception as e:
        print(f"[ERRO] Falha na conexão SSH com {ip}: {e}")
        return None


def fechar_ssh(client):
    if client:
        client.close()
        print("[OK] Conexão encerrada.")