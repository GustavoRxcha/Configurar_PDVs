from modulos.conexao_ssh import conectar_ssh, fechar_ssh
from modulos.transferir_arquivos import transferir_arquivos_para_caixa
from modulos.permissoes import configurar_permissoes
from modulos.descompactar_arquivos import descompactar_arquivos
from modulos.mover_bibliotecas import mover_bibliotecas
from modulos.editar_fstab import editar_fstab
from modulos.restaurar_banco import restaurar_banco

ip_terminal = input("Digite o IP do terminal Caixa: ")
uf_filial = input("Digite a UF da filial (ex: PR, SP, RJ): ")
numero_caixa = input("Digite o número do caixa: ")

ssh = conectar_ssh(ip_terminal)
if ssh:
    # Transferir arquivos
    arquivos = ["backups/Banco_PDV.zip", "backups/Schemas.zip", "backups/libclisitef.so", "backups/libclisitef64.so", "backups/libemv64.so", "backups/libqrencode64.so",]
    transferir_arquivos_para_caixa(ssh, arquivos)

    # Configurar permissões
    configurar_permissoes(ssh)

    # Descompactar arquivos
    descompactar_arquivos(ssh)

    # Mover bibliotecas para /usr/lib
    mover_bibliotecas(ssh)

    # Editar fstab com o IP do caixa e a UF da filial
    editar_fstab(ssh, ip_terminal, uf_filial)

    # Restaurar banco de dados
    restaurar_banco(ip_terminal, numero_caixa)

    # Fechar conexão SSH
    fechar_ssh(ssh)