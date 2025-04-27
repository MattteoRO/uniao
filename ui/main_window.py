# -*- coding: utf-8 -*-

"""
Janela principal da aplicação
Define a estrutura de abas e gerencia a navegação entre elas.
"""

import tkinter as tk
from tkinter import ttk
import logging

from ui.painel_tab import PainelTab
from ui.servico_tab import ServicoTab
from ui.mecanico_tab import MecanicoTab
from ui.configuracoes_tab import ConfiguracoesTab
from ui.relatorios_tab import RelatoriosTab

logger = logging.getLogger(__name__)

class MainWindow:
    """
    Classe que representa a janela principal da aplicação.
    Gerencia o sistema de abas e navegação entre telas.
    """
    
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        logger.info("Janela principal inicializada")
    
    def setup_ui(self):
        """Configura a interface da janela principal."""
        # Configurações gerais
        self.root.configure(padx=10, pady=10)
        
        # Configura estilo
        self.style = ttk.Style()
        self.style.configure('TNotebook', tabposition='n')
        self.style.configure('TNotebook.Tab', padding=[20, 5], font=('Arial', 11, 'bold'))
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Large.TButton', font=('Arial', 12))
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cabeçalho com logo (usando texto como placeholder)
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.logo_label = ttk.Label(
            self.header_frame, 
            text="MONARK MOTOPEÇAS E BICICLETARIA",
            style='Header.TLabel'
        )
        self.logo_label.pack(side=tk.LEFT, padx=10)
        
        # Notebook (sistema de abas)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Criação das abas
        self.tabs = {}
        
        # Aba Painel (menu principal)
        self.tabs['painel'] = PainelTab(self.notebook, self)
        self.notebook.add(self.tabs['painel'], text="Painel")
        
        # Aba Serviço
        self.tabs['servico'] = ServicoTab(self.notebook, self)
        self.notebook.add(self.tabs['servico'], text="Serviço")
        
        # Aba Mecânico
        self.tabs['mecanico'] = MecanicoTab(self.notebook, self)
        self.notebook.add(self.tabs['mecanico'], text="Mecânico")
        
        # Aba Configurações
        self.tabs['configuracoes'] = ConfiguracoesTab(self.notebook, self)
        self.notebook.add(self.tabs['configuracoes'], text="Configurações")
        
        # Aba Relatórios
        self.tabs['relatorios'] = RelatoriosTab(self.notebook, self)
        self.notebook.add(self.tabs['relatorios'], text="Relatórios")
        
        # Barra de status
        self.status_bar = ttk.Label(self.main_frame, text="Sistema inicializado", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # Bind para eventos de mudança de aba
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        """Evento disparado quando o usuário muda de aba."""
        tab_id = self.notebook.select()
        tab_name = self.notebook.tab(tab_id, "text")
        logger.debug(f"Mudou para a aba: {tab_name}")
        
        # Atualiza a interface da aba selecionada
        for name, tab in self.tabs.items():
            if tab_name.lower() == name.lower() and hasattr(tab, 'on_tab_selected'):
                tab.on_tab_selected()
    
    def navigate_to(self, tab_name, **kwargs):
        """
        Navega para uma aba específica.
        
        Args:
            tab_name (str): Nome da aba para navegar
            **kwargs: Argumentos adicionais para passar para a aba
        """
        tab_index = {"painel": 0, "servico": 1, "mecanico": 2, "configuracoes": 3, "relatorios": 4}
        
        if tab_name in tab_index:
            # Seleciona a aba
            self.notebook.select(tab_index[tab_name])
            
            # Chama o método on_navigate da aba, se existir
            if hasattr(self.tabs[tab_name], 'on_navigate'):
                self.tabs[tab_name].on_navigate(**kwargs)
            
            logger.debug(f"Navegou para: {tab_name} com argumentos: {kwargs}")
    
    def set_status(self, message):
        """Atualiza a mensagem na barra de status."""
        self.status_bar.config(text=message)
