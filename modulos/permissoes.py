import paramiko

def configurar_permissoes(ssh_client):
    
    try:
        comandos = [
            "sudo chown -R prevenda.prevenda /opt",
            "sudo chmod -R 777 /opt"
        ]

        for cmd in comandos:
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            erro = stderr.read().decode()

            if erro:
                print(f"[ERRO] Comando '{cmd}' falhou: {erro}")
                return False
            else:
                print(f"[OK] Comando '{cmd}' executado com sucesso.")
        return True
    
    except Exception as e:
        print(f"[ERRO] Falha ao configurar permissões: {e}")
        return False
