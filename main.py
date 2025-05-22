import pyodbc
import threading
from tkinter import *
from style import *
from style.cores import *
from dotenv import load_dotenv
import os
from PIL import Image, ImageTk

################################################################################################################

from modulos.conexao_ssh import conectar_ssh, fechar_ssh
from modulos.transferir_arquivos import transferir_arquivos_para_opt, transferir_arquivos_para_pdv
from modulos.permissoes import configurar_permissoes
from modulos.descompactar_arquivos import descompactar_arquivos
from modulos.mover_bibliotecas import mover_bibliotecas
from modulos.editar_fstab import editar_fstab
from modulos.restaurar_banco import restaurar_banco
from modulos.restaurar_banco import executar_usp
import time

################################################################################################################
class AplicacaoConfigPDV(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Configuração de Caixas")
        self.iconbitmap("style/EFico.ico")
        self.geometry("420x510")
        self.configure(bg=fundo)

        logo = Image.open("style/EFlogo.png")  # Substitua pelo caminho correto da sua imagem
        logo = logo.resize((620, 130))
        self.logo_tk = ImageTk.PhotoImage(logo)

        # Container principal
        container = Frame(self, bg=fundo)
        container.pack(fill="both", expand=True)
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        self.telas = {}
                                                                                               
        for T in (ConfigurarCaixa,):
            tela = T(container, self)
            self.telas[T] = tela
            tela.grid(row=0, column=0, sticky="nsew")
        
        # Mostra a Home
        self.mostrar_tela(ConfigurarCaixa)
    
    def mostrar_tela(self, tela_class):
        tela = self.telas[tela_class]

        if hasattr(tela, 'atualizar'):
            tela.atualizar()

        tela.tkraise()

################################################################################################################

class ConfigurarCaixa(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent, bg=fundo)
        self.controller = controller

        # Título da tela
        self.titulo_configuracao = Label(self, text="| Configuração de Caixas |", bg=fundo, fg=tags, font=("Arial", 20, "bold"))
        self.titulo_configuracao.pack(pady=(5, 30))

        # Campo de IP
        frame_ip = Frame(self, bg=fundo)
        frame_ip.pack(pady=(5, 5))
        Label(frame_ip, text="IP:", bg=fundo, fg=cor_texto, font=("Arial", 13, "bold")).pack(side=LEFT, padx=(0, 10))
        self.inserir_ip = Entry(frame_ip, fg='grey', width=15, font=("Arial", 13))
        self.inserir_ip.insert(0, 'Informe o IP...')
        self.inserir_ip.bind('<FocusIn>', self.limpar_placeholder)
        self.inserir_ip.pack(side=LEFT, padx=(0, 44))

        # Campo de Caixa
        frame_caixa = Frame(self, bg=fundo)
        frame_caixa.pack(pady=(5, 5))
        Label(frame_caixa, text="Caixa:", bg=fundo, fg=cor_texto, font=("Arial", 13, "bold")).pack(side=LEFT, padx=(0, 10))
        self.inserir_caixa = Entry(frame_caixa, fg='grey', width=15, font=("Arial", 13))
        self.inserir_caixa.insert(0, 'Informe o CAIXA...')
        self.inserir_caixa.bind('<FocusIn>', self.limpar_placeholder)
        self.inserir_caixa.pack(side=LEFT, padx=(0, 72))

        # Campo de UF
        frame_uf = Frame(self, bg=fundo)
        frame_uf.pack(pady=(5, 5))
        Label(frame_uf, text="UF:", bg=fundo, fg=cor_texto, font=("Arial", 13, "bold")).pack(side=LEFT, padx=(0, 10))
        self.inserir_uf = Entry(frame_uf, fg='grey', width=15, font=("Arial", 13))
        self.inserir_uf.insert(0, 'Informe a UF...')
        self.inserir_uf.bind('<FocusIn>', self.limpar_placeholder)
        self.inserir_uf.pack(side=LEFT, padx=(0, 50))

        # Status da configuração
        self.status_configuracao = Label(self, text="", bg=fundo, fg=cor_texto, font=("Arial", 13, "bold"), anchor="center", justify="center", wraplength=500)
        self.status_configuracao.pack(pady=5, fill='x')

        self.erro_configuracao = Label(self, text="", bg=fundo, fg=vermelho, font=("Arial", 13, "bold"), anchor="center", justify="center", wraplength=500)
        self.erro_configuracao.pack(pady=5, fill='x')

        # Botão de configuração
        self.botao_configurar = Button(self, text="Iniciar Configuração", width=20, height=1, bg=botao1, fg="#ffffff", bd=3, relief="ridge", font=("Arial", 13), command=self.iniciar_configuracao)
        self.botao_configurar.pack(pady=(20, 20))
        aplicar_hover(self.botao_configurar, hover, botao1)


    def limpar_placeholder(self, event):
        widget = event.widget
        if widget.get() in ['Informe o IP...', 'Informe o CAIXA...', 'Informe a UF...']:
            widget.delete(0, END)
            widget.config(fg='black')

    def iniciar_configuracao(self):
        self.status_configuracao.config(text="")
        self.erro_configuracao.config(text= "")
        self.botao_configurar.pack_forget()
        ip_terminal = self.inserir_ip.get().strip()
        numero_caixa = self.inserir_caixa.get().strip()
        uf_filial = self.inserir_uf.get().strip()

        if not ip_terminal or not numero_caixa or not uf_filial:
            self.botao_configurar.pack(pady=(20, 20))
            self.erro_configuracao.config(text= "Erro: Preencha todos os campos corretamente.")
            return

        self.inserir_ip.delete(0, END)
        self.inserir_caixa.delete(0, END)
        self.inserir_uf.delete(0, END)

        # Executa a configuração em uma thread separada
        threading.Thread(target=self.configurar_em_thread, args=(ip_terminal, numero_caixa, uf_filial)).start()

    def configurar_em_thread(self, ip_terminal, numero_caixa, uf_filial):
        try:
            from modulos.conexao_ssh import conectar_ssh, fechar_ssh
            from modulos.transferir_arquivos import transferir_arquivos_para_opt, transferir_arquivos_para_pdv
            from modulos.permissoes import configurar_permissoes
            from modulos.descompactar_arquivos import descompactar_arquivos
            from modulos.mover_bibliotecas import mover_bibliotecas
            from modulos.editar_fstab import editar_fstab
            from modulos.restaurar_banco import restaurar_banco
            import time

            ssh = conectar_ssh(ip_terminal)
            if ssh == False:
                self.botao_configurar.pack(pady=(20, 20))
                self.erro_configuracao.config(text= "Erro: Falha na conexão")
                return
            else:
                self.atualizar_status("Executando a configuração do caixa...")

                # Transferir arquivos
                arquivos_opt = ["backups/Banco_PDV.zip", "backups/libclisitef.so", "backups/libclisitef64.so", "backups/libemv64.so", "backups/libqrencode64.so"]
                arquivos_pdv = ["backups/Schemas.zip"]
                transferir_arquivos_para_opt(ssh, arquivos_opt)
                transferir_arquivos_para_pdv(ssh, arquivos_pdv)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\naguarde configurando...")

                # Configurar permissões
                configurar_permissoes(ssh)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\n2° - Permissões configuradas com sucesso!\naguarde configurando...")

                # Descompactar arquivos
                descompactar_arquivos(ssh)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\n2° - Permissões configuradas com sucesso!\n3° - Arquivos descompactados com sucesso!\naguarde configurando...")
                time.sleep(4)

                # Mover bibliotecas
                mover_bibliotecas(ssh)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\n2° - Permissões configuradas com sucesso!\n3° - Arquivos descompactados com sucesso!\n4° - Bibliotecas movidas com sucesso!\naguarde configurando...")

                # Editar fstab
                editar_fstab(ssh, ip_terminal, uf_filial)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\n2° - Permissões configuradas com sucesso!\n3° - Arquivos descompactados com sucesso!\n4° - Bibliotecas movidas com sucesso!\n5° - Configuração do fstab concluída!\naguarde configurando...")

                # Restaurar banco de dados
                restaurar_banco(ssh, ip_terminal)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\n2° - Permissões configuradas com sucesso!\n3° - Arquivos descompactados com sucesso!\n4° - Bibliotecas movidas com sucesso!\n5° - Configuração do Nano (fstab) concluída!\n6° - Banco de dados restaurado com sucesso!\naguarde configurando...")

                # Executar USP
                executar_usp(ip_terminal, numero_caixa)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\n2° - Permissões configuradas com sucesso!\n3° - Arquivos descompactados com sucesso!\n4° - Bibliotecas movidas com sucesso!\n5° - Configuração do fstab concluída!\n6° - Banco de dados restaurado com sucesso!\n7° - Executado USP de restauração e CTRL + T\naguarde configurando...")

                # Fechar conexão SSH
                fechar_ssh(ssh)
                self.atualizar_status("Executando a configuração do caixa...\n\n1° - Transferência de arquivos concluída!\n2° - Permissões configuradas com sucesso!\n3° - Arquivos descompactados com sucesso!\n4° - Bibliotecas movidas com sucesso!\n5° - Configuração do fstab concluída!\n6° - Banco de dados restaurado com sucesso!\n7° - Executado USP de restauração e CTRL + T\n\nProcesso de configuração concluído com sucesso!")
                self.botao_configurar.pack(pady=(20, 20))
        except Exception as e:
            self.botao_configurar.pack(pady=(20, 20))
            self.erro_configuracao.config(text= f"Erro: {str(e)}")
            return

    def atualizar_status(self, mensagem):
        """Atualiza o status na interface gráfica."""
        self.status_configuracao.config(text=mensagem)
        self.update_idletasks()

################################################################################################################

if __name__ == "__main__":
    app = AplicacaoConfigPDV()
    app.mainloop()