from scp import SCPClient
from modulos.conexao_ssh import conectar_ssh

def transferir_arquivos_para_caixa(ssh_client, local_paths, remote_path="/opt"):

    try:
        with SCPClient(ssh_client.get_transport()) as scp:
            for path in local_paths:

                if "Schemas.zip" in path:
                    destino = "/opt/pdv"  # Envia Schemas.zip para /opt/pdv
                else:
                    destino = remote_path  # Outros arquivos vão para /opt

                print(f"[INFO] Enviando {path} para {destino}...")
                scp.put(path, recursive=True, remote_path=remote_path)
        print("[OK] Todos os arquivos foram transferidos com sucesso.")

    except Exception as e:
        print(f"[ERRO] Falha ao transferir arquivos: {e}")