# modulos/descompactar_arquivos.py

import paramiko

def descompactar_arquivos(ssh_client, remote_path="/opt"):
    
    try:
        # Comandos para identificar e descompactar arquivos
        comandos = [
            "cd /opt && unzip Banco_PDV.zip",  # Descompacta o backup do banco
            "cd /opt/pdv && rm -rf schemas",  # Exclui a pasta 'schemas'
            "cd /opt/pdv && unzip Schemas.zip"  # Descompacta os schemas
        ]

        for cmd in comandos:
            print(f"[INFO] Executando comando: {cmd}")
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            erro = stderr.read().decode()

            if erro:
                print(f"[ERRO] Falha ao executar '{cmd}': {erro}")
            else:
                print(f"[OK] Comando '{cmd}' executado com sucesso.")

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante descompactação: {e}")