import paramiko

def editar_fstab(ssh_client, ip_caixa, uf_filial):
    """
    Edita o arquivo /etc/fstab, substituindo 'estado' pela UF da filial e 'drogariasnisse.net' pelo IP do caixa.
    """
    try:
        # Comando para substituir 'estado' pela UF da filial
        comando_estado = f"sudo sed -i 's/estado/{uf_filial}/g' /etc/fstab"
        print(f"Executando comando: {comando_estado}")
        stdin, stdout, stderr = ssh_client.exec_command(comando_estado)
        erro_estado = stderr.read().decode()

        if erro_estado:
            print(f"[ERRO] Falha ao substituir 'estado': {erro_estado}")
        else:
            print(f"[OK] Substituição de 'estado' por '{uf_filial}' concluída com sucesso.")

        # Comando para substituir 'drogariasnissei.net' pelo IP do caixa
        comando_drogarias = f"sudo sed -i 's/drogariasnissei.net/{ip_caixa}/g' /etc/fstab"
        print(f"Executando comando: {comando_drogarias}")
        stdin, stdout, stderr = ssh_client.exec_command(comando_drogarias)
        erro_drogarias = stderr.read().decode()

        if erro_drogarias:
            print(f"[ERRO] Falha ao substituir 'drogariasnisse.net': {erro_drogarias}")
        else:
            print(f"[OK] Substituição de 'drogariasnisse.net' por '{ip_caixa}' concluída com sucesso.")

    except Exception as e:
        print(f"[EXCEÇÃO] Erro durante a edição do fstab: {e}")