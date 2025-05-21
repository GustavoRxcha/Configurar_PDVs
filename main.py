from modulos.conexao_ssh import conectar_ssh, fechar_ssh
from modulos.transferir_arquivos import transferir_arquivos_para_opt, transferir_arquivos_para_pdv
from modulos.permissoes import configurar_permissoes
from modulos.descompactar_arquivos import descompactar_arquivos
from modulos.mover_bibliotecas import mover_bibliotecas
from modulos.editar_fstab import editar_fstab
from modulos.restaurar_banco import restaurar_banco
import time

ip_terminal = input("Digite o IP do terminal Caixa: ")
uf_filial = input("Digite a UF da filial (ex: PR, SC, SP, GO): ")
numero_caixa = input("Digite o número do caixa: ")

ssh = conectar_ssh(ip_terminal)


# Transferir arquivos TESTAR EM OUTRAS PASTAS ENVIAR OUTROS TIPOS DE ARQUIVOS QUE NÃO AFETARÃO OS CAIXAS.
arquivos_opt = ["backups/Banco_PDV.zip", "backups/libclisitef.so", "backups/libclisitef64.so", "backups/libemv64.so", "backups/libqrencode64.so", ]
arquivos_pdv = ["backups/Schemas.zip",]
transferir_arquivos_para_opt(ssh, arquivos_opt)
transferir_arquivos_para_pdv(ssh, arquivos_pdv)


# Configurar permissões
configurar_permissoes(ssh)


# Descompactar arquivos ENVIAR ALGUM ARQUIVO .ZIP PELA FUNÇÃO DE TRANSFERIR E TESTAR A FUNÇÃO DE DESCOMPACTAR EM ALGUAM PASTA QUE NÃO AFETARÁ O CAIXA.
descompactar_arquivos(ssh)
time.sleep(4)

# Mover bibliotecas para /usr/lib TENTAR MOVER ALGUM ARQUIVO TESTE ENTRE PASTAS QUE NÃO IRÃO CAUSAR PROBLEMA NO CAIXA PARA DEPOIS MOVER AS LIBS DA OPT PARA /usr/lib.
mover_bibliotecas(ssh)

#CORRETO
# Editar fstab com o IP do caixa e a UF da filial VERIFICAR QUAIS SÃO OS TEXTOS REFERENTES A 'UF' E AO 'IP CAIXA' PARA CORRIIR NA FUNÇÃO E FAZER TESTE SE ELE EDITA CORRETAMENTE.
editar_fstab(ssh, ip_terminal, uf_filial)


# Restaurar banco de dados REALIZAR TESTE EM CASA NO BANCO TESTE OU EM ALGUM CAIXA JÁ COM DEFEITO.
restaurar_banco(ssh, ip_terminal, numero_caixa)

# Fechar conexão SSH
fechar_ssh(ssh)