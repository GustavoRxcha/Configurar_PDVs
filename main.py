from modulos.conexao_ssh import conectar_ssh, fechar_ssh
from modulos.transferir_arquivos import transferir_arquivos_para_caixa
from modulos.permissoes import configurar_permissoes
from modulos.descompactar_arquivos import descompactar_arquivos

ip_terminal = "192.168.0.105"  # Exemplo de IP

ssh = conectar_ssh(ip_terminal)
if ssh:
    # Transferir arquivos
    arquivos = ["backups/Banco_PDV.zip", "backups/Schemas.zip", "backups/bkp", "backups/libs"]
    transferir_arquivos_para_caixa(ssh, arquivos)

    # Configurar permissões
    configurar_permissoes(ssh)

    # Descompactar arquivos
    descompactar_arquivos(ssh)

    # Fechar conexão SSH
    fechar_ssh(ssh)