# -*- coding: utf-8 -*-

"""
Aba Painel
Exibe o menu principal da aplicação com botões para as principais funcionalidades.
"""

import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger(__name__)

class PainelTab(ttk.Frame):
    """
    Classe que representa a aba Painel, que contém o menu principal da aplicação.
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
        logger.debug("Aba Painel inicializada")
    
    def setup_ui(self):
        """Configura a interface da aba Painel."""
        # Container principal
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        title_label = ttk.Label(
            self.main_container,
            text="Bem-vindo ao Sistema de Gerenciamento",
            font=('Arial', 18, 'bold')
        )
        title_label.pack(pady=(0, 30))
        
        # Grid de botões principais
        self.buttons_frame = ttk.Frame(self.main_container)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configura linhas e colunas para centralizar
        self.buttons_frame.columnconfigure(0, weight=1)
        self.buttons_frame.columnconfigure(1, weight=1)
        self.buttons_frame.columnconfigure(2, weight=1)
        self.buttons_frame.rowconfigure(0, weight=1)
        self.buttons_frame.rowconfigure(1, weight=1)
        self.buttons_frame.rowconfigure(2, weight=1)
        
        # Estilo para botões
        self.style = ttk.Style()
        self.style.configure('Menu.TButton', font=('Arial', 14, 'bold'), padding=20)
        
        # Botões principais
        self.create_menu_button(
            "Novo Serviço",
            "Cadastrar um novo serviço",
            self.on_new_service_click,
            0, 1
        )
        
        self.create_menu_button(
            "Gerenciar Mecânicos",
            "Cadastrar e editar mecânicos",
            self.on_mechanics_click,
            1, 0
        )
        
        self.create_menu_button(
            "Relatórios",
            "Visualizar e exportar relatórios",
            self.on_reports_click,
            1, 2
        )
        
        self.create_menu_button(
            "Carteiras Digitais",
            "Gerenciar carteiras de mecânicos e loja",
            self.on_wallets_click,
            2, 1
        )
    
    def create_menu_button(self, text, tooltip, command, row, column):
        """
        Cria um botão de menu estilizado com ícone e tooltip.
        
        Args:
            text (str): Texto do botão
            tooltip (str): Texto de ajuda ao passar o mouse
            command (function): Função chamada ao clicar no botão
            row (int): Linha na grid
            column (int): Coluna na grid
        """
        button_frame = ttk.Frame(self.buttons_frame)
        button_frame.grid(row=row, column=column, padx=20, pady=20, sticky="nsew")
        
        # Botão principal
        button = ttk.Button(
            button_frame,
            text=text,
            command=command,
            style='Menu.TButton'
        )
        button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tooltip
        self.create_tooltip(button, tooltip)
    
    def create_tooltip(self, widget, text):
        """
        Cria um tooltip simples para um widget.
        
        Args:
            widget: Widget ao qual associar o tooltip
            text (str): Texto do tooltip
        """
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Cria uma janela top-level
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(
                self.tooltip, text=text, background="#FFFFDD",
                relief=tk.SOLID, borderwidth=1, padding=(5, 3)
            )
            label.pack()
        
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def on_new_service_click(self):
        """Evento disparado ao clicar no botão Novo Serviço."""
        logger.debug("Botão Novo Serviço clicado")
        self.main_window.navigate_to("servico", action="new")
    
    def on_mechanics_click(self):
        """Evento disparado ao clicar no botão Gerenciar Mecânicos."""
        logger.debug("Botão Gerenciar Mecânicos clicado")
        self.main_window.navigate_to("mecanico")
    
    def on_reports_click(self):
        """Evento disparado ao clicar no botão Relatórios."""
        logger.debug("Botão Relatórios clicado")
        self.main_window.navigate_to("relatorios")
    
    def on_wallets_click(self):
        """Evento disparado ao clicar no botão Carteiras Digitais."""
        logger.debug("Botão Carteiras Digitais clicado")
        self.main_window.navigate_to("mecanico", show_carteiras=True)
    
    def on_tab_selected(self):
        """Método chamado quando a aba é selecionada."""
        self.main_window.set_status("Menu Principal")
