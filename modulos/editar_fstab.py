import paramiko
import time
from modulos.conexao_ssh import conectar_ssh

def editar_fstab(ssh_client, ip_caixa, uf_filial):

    try:
        base_ip = ".".join(ip_caixa.split(".")[:-1])  # Pega "10.16.50"
        ip_servidor = f"{base_ip}.24"

        # Define o novo conteúdo do fstab
        novo_conteudo = f"""# /etc/fstab: static file system information.
#
# Use 'blkid' to print the universally unique identifier for a
# device; this may be used with UUID= as a more robust way to name devices
# that works even if disks are added and removed. See fstab(5).
#
# <file system> <mount point>   <type>  <options>       <dump>  <pass>
/dev/mapper/ubuntu--vg-root /               ext4    errors=remount-ro 0       1
# /boot was on /dev/sda1 during installation
UUID=e2ebba31-2fdd-4d4c-a770-eacec48ae423 /boot           ext2    defaults        0       2
/dev/mapper/ubuntu--vg-swap none            swap    sw              0       0

# ftp procfit
nasprocfit.intra.drogariasnissei.com.br:/nfs/procftp/{uf_filial.lower()} /mnt/procftp nfs ro,noauto,hard,intr,noexec,users,noatime,nolock,bg,tcp,actimeo=1800 0 0
//{ip_servidor}/PDV01 /mnt/PBM/vidalink/ cifs vers=2.0,username=frente,password=Nissei1,user,dir_mode=0777,file_mode=0777 0 0
"""

        # Função auxiliar para enviar comandos como root
        def enviar_comando_com_root(shell, comando, timeout=30):
            output = ""
            start_time = time.time()

            shell.send("su root\n")
            time.sleep(1)  
            shell.send("F@RM4C1A\n")  
            time.sleep(2)  

            # Verificar se a autenticação foi bem-sucedida
            while not output.endswith("# "):  # Espera pelo prompt do root (#)
                if shell.recv_ready():
                    chunk = shell.recv(1024).decode('utf-8', errors='ignore')
                    output += chunk
                    print(f"Saida parcial:\n{chunk}")
                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout ao autenticar como root.")
                time.sleep(0.5)

            print(f"Executando comando: {comando}")
            shell.send(comando + "\n")
            time.sleep(4)

            # Capturar a saída do comando
            output = ""
            while True:
                if shell.recv_ready():
                    chunk = shell.recv(1024).decode('utf-8', errors='ignore')
                    output += chunk
                    print(f"Saida parcial:\n{chunk}")

                # Verificar se o comando foi concluído (prompt #)
                if output.endswith("# "):
                    print("Comando concluído.")
                    break

                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout ao executar o comando.")
                time.sleep(0.5)

            return

        # Abrir uma sessão interativa
        shell = ssh_client.invoke_shell()

        # Comando para escrever o novo conteúdo no arquivo /etc/fstab
        comando_escrever_fstab = f"echo '{novo_conteudo}' | tee /etc/fstab > /dev/null"
        print("Recriando o arquivo /etc/fstab...")
        enviar_comando_com_root(shell, comando_escrever_fstab)

        print("\n[OK] Arquivo fstab recriado com sucesso.\n")

        # Valida o arquivo fstab
        print("Validando o arquivo fstab...")
        shell.send("mount -a\n")
        print("[OK] Arquivo fstab validado com sucesso.\n")
        time.sleep(2)

        shell.send("exit\n")

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante a edição do fstab: {e}\n")