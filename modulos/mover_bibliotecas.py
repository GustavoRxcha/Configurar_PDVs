import paramiko
from modulos.conexao_ssh import conectar_ssh

def mover_bibliotecas(ssh_client, origem="/opt", destino="/usr/lib"):
    
    try:
        # Lista de bibliotecas a serem movidas
        bibliotecas = [
            "libclisitef.so",
            "libclisitef64.so",
            "libemv64.so",
            "libqrencode64.so"
        ]

        for lib in bibliotecas:
            comando = f"mv {origem}/{lib} {destino}"
            print(f"Executando comando: {comando}")
            stdin, stdout, stderr = ssh_client.exec_command(comando)
            erro = stderr.read().decode()

            if erro:
                print(f"[ERRO] Falha ao mover '{lib}': {erro}")
            else:
                print(f"[OK] Biblioteca '{lib}' movida com sucesso.")

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante a movimentação das bibliotecas: {e}")