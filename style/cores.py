from tkinter import Button

fundo = '#292929'
cor_texto = '#f0f6fc'
botao1 = '#7150cd'
botao2 = "#6b7fe2"
hover = "#948be2"
borda = '#d1d5db'
tags = "#7577f1"
vermelho = '#e64a19'
verde = '#398636'

def aplicar_hover(botao, cor_hover, cor_normal):
    botao.bind("<Enter>", lambda e: e.widget.config(bg=cor_hover))
    botao.bind("<Leave>", lambda e: e.widget.config(bg=cor_normal))

def aplicar_hover_em_todos(frame, cor_hover, cor_original):
    for widget in frame.winfo_children():
        if isinstance(widget, Button):
            widget.bind("<Enter>", lambda e, c=cor_hover: e.widget.config(bg=c))
            widget.bind("<Leave>", lambda e, c=cor_original: e.widget.config(bg=c))