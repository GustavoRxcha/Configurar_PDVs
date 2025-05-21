from scp import SCPClient
from modulos.conexao_ssh import conectar_ssh

def transferir_arquivos_para_opt(ssh_client, local_paths, remote_path="/opt"):

    try:
        with SCPClient(ssh_client.get_transport()) as scp:
            for path in local_paths:

                print(f"[INFO] Enviando {path} para {remote_path}...")
                scp.put(path, recursive=True, remote_path=remote_path)

    except Exception as e:
        print(f"[ERRO] Falha ao transferir arquivos: {e}\n")

def transferir_arquivos_para_pdv(ssh_client, local_paths, remote_path="/opt/pdv"):

    try:
        with SCPClient(ssh_client.get_transport()) as scp:
            for path in local_paths:

                print(f"[INFO] Enviando {path} para {remote_path}...")
                scp.put(path, recursive=True, remote_path=remote_path)
        print("[OK] Todos os arquivos foram transferidos com sucesso.\n")

    except Exception as e:
        print(f"[ERRO] Falha ao transferir arquivos: {e}\n")