# -*- coding: utf-8 -*-

"""
Aba Configurações
Permite configurar opções gerais do sistema.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import os

from models import Configuracao

logger = logging.getLogger(__name__)

class ConfiguracoesTab(ttk.Frame):
    """
    Classe que representa a aba Configurações, onde é possível definir opções do sistema.
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
        logger.debug("Aba Configurações inicializada")
    
    def setup_ui(self):
        """Configura a interface da aba Configurações."""
        # Container principal
        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            self.main_container,
            text="Configurações do Sistema",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Frame para configurações gerais
        config_frame = ttk.LabelFrame(self.main_container, text="Configurações Gerais")
        config_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # Layout em grid para os campos
        inner_frame = ttk.Frame(config_frame, padding=10)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nome da Empresa
        row = 0
        ttk.Label(inner_frame, text="Nome da Empresa:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.nome_empresa_var = tk.StringVar()
        ttk.Entry(inner_frame, width=40, textvariable=self.nome_empresa_var).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Endereço
        row += 1
        ttk.Label(inner_frame, text="Endereço:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.endereco_var = tk.StringVar()
        ttk.Entry(inner_frame, width=40, textvariable=self.endereco_var).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Telefone
        row += 1
        ttk.Label(inner_frame, text="Telefone:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.telefone_var = tk.StringVar()
        ttk.Entry(inner_frame, width=20, textvariable=self.telefone_var).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Caminho do CSV
        row += 1
        ttk.Label(inner_frame, text="Arquivo CSV de Peças:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        csv_frame = ttk.Frame(inner_frame)
        csv_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.caminho_csv_var = tk.StringVar()
        ttk.Entry(csv_frame, width=30, textvariable=self.caminho_csv_var).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            csv_frame, 
            text="Procurar...", 
            command=self.browse_csv
        ).pack(side=tk.LEFT)
        
        # Frame para diretórios de exportação
        dir_frame = ttk.LabelFrame(self.main_container, text="Diretórios de Exportação de PDFs")
        dir_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # Layout em grid para os diretórios
        dir_inner_frame = ttk.Frame(dir_frame, padding=10)
        dir_inner_frame.pack(fill=tk.BOTH, expand=True)
        
        # Diretório de PDFs para Cliente
        row = 0
        ttk.Label(dir_inner_frame, text="PDFs Cliente:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.dir_cliente_var = tk.StringVar(value="ser cliente")
        
        dir_cliente_frame = ttk.Frame(dir_inner_frame)
        dir_cliente_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Entry(dir_cliente_frame, width=30, textvariable=self.dir_cliente_var).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            dir_cliente_frame, 
            text="Procurar...", 
            command=lambda: self.browse_directory(self.dir_cliente_var)
        ).pack(side=tk.LEFT)
        
        # Diretório de PDFs para Mecânico
        row += 1
        ttk.Label(dir_inner_frame, text="PDFs Mecânico:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.dir_mecanico_var = tk.StringVar(value="ser mecanico")
        
        dir_mecanico_frame = ttk.Frame(dir_inner_frame)
        dir_mecanico_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Entry(dir_mecanico_frame, width=30, textvariable=self.dir_mecanico_var).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            dir_mecanico_frame, 
            text="Procurar...", 
            command=lambda: self.browse_directory(self.dir_mecanico_var)
        ).pack(side=tk.LEFT)
        
        # Diretório de PDFs para Loja
        row += 1
        ttk.Label(dir_inner_frame, text="PDFs Loja:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.dir_loja_var = tk.StringVar(value="ser loja")
        
        dir_loja_frame = ttk.Frame(dir_inner_frame)
        dir_loja_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Entry(dir_loja_frame, width=30, textvariable=self.dir_loja_var).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            dir_loja_frame, 
            text="Procurar...", 
            command=lambda: self.browse_directory(self.dir_loja_var)
        ).pack(side=tk.LEFT)
        
        # Verifica se os diretórios existem e cria se necessário
        self.check_directories()
        
        # Separador
        ttk.Separator(self.main_container, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Botões de ação
        buttons_frame = ttk.Frame(self.main_container)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame,
            text="Restaurar Padrões",
            command=self.restore_defaults
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="Salvar Configurações",
            command=self.save_config
        ).pack(side=tk.RIGHT, padx=5)
        
        # Carrega as configurações atuais
        self.load_config()
    
    def load_config(self):
        """Carrega as configurações atuais do banco de dados."""
        try:
            config = Configuracao.get()
            
            if config:
                self.nome_empresa_var.set(config['nome_empresa'])
                self.endereco_var.set(config['endereco'])
                self.telefone_var.set(config['telefone'])
                self.caminho_csv_var.set(config['caminho_csv'])
            else:
                # Configurações padrão
                self.restore_defaults(show_message=False)
                
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar configurações: {str(e)}")
    
    def save_config(self):
        """Salva as configurações no banco de dados."""
        try:
            # Valida o caminho do CSV
            caminho_csv = self.caminho_csv_var.get().strip()
            if not os.path.isfile(caminho_csv):
                if not messagebox.askyesno(
                    "Arquivo CSV Não Encontrado",
                    f"O arquivo '{caminho_csv}' não foi encontrado. "
                    "Deseja salvar o caminho mesmo assim?"
                ):
                    return
            
            # Cria os diretórios se não existirem
            self.create_directories()
            
            # Atualiza as configurações
            Configuracao.update(
                nome_empresa=self.nome_empresa_var.get().strip(),
                endereco=self.endereco_var.get().strip(),
                telefone=self.telefone_var.get().strip(),
                caminho_csv=caminho_csv
            )
            
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {str(e)}")
    
    def browse_csv(self):
        """Abre o diálogo para selecionar o arquivo CSV."""
        filename = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV",
            filetypes=(("Arquivos CSV", "*.csv"), ("Todos os Arquivos", "*.*"))
        )
        
        if filename:
            self.caminho_csv_var.set(filename)
    
    def browse_directory(self, var):
        """
        Abre o diálogo para selecionar um diretório.
        
        Args:
            var (tk.StringVar): Variável que armazenará o caminho selecionado
        """
        directory = filedialog.askdirectory(title="Selecionar Diretório")
        
        if directory:
            var.set(directory)
    
    def restore_defaults(self, show_message=True):
        """
        Restaura as configurações para os valores padrão.
        
        Args:
            show_message (bool): Se True, exibe mensagem de confirmação
        """
        if show_message and not messagebox.askyesno(
            "Restaurar Padrões",
            "Deseja realmente restaurar todas as configurações para os valores padrão?"
        ):
            return
        
        # Configurações padrão
        self.nome_empresa_var.set("Monark Motopeças e Bicicletaria")
        self.endereco_var.set("")
        self.telefone_var.set("")
        self.caminho_csv_var.set("bdmonarkbd.csv")
        self.dir_cliente_var.set("ser cliente")
        self.dir_mecanico_var.set("ser mecanico")
        self.dir_loja_var.set("ser loja")
        
        if show_message:
            messagebox.showinfo(
                "Padrões Restaurados",
                "As configurações foram restauradas para os valores padrão.\n\n"
                "Clique em 'Salvar Configurações' para aplicar as mudanças."
            )
    
    def check_directories(self):
        """Verifica se os diretórios de exportação existem e cria se necessário."""
        directories = [
            "ser cliente",
            "ser mecanico",
            "ser loja"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logger.info(f"Diretório criado: {directory}")
                except Exception as e:
                    logger.error(f"Erro ao criar diretório {directory}: {e}")
    
    def create_directories(self):
        """Cria os diretórios de exportação se não existirem."""
        directories = [
            self.dir_cliente_var.get().strip(),
            self.dir_mecanico_var.get().strip(),
            self.dir_loja_var.get().strip()
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logger.info(f"Diretório criado: {directory}")
                except Exception as e:
                    logger.error(f"Erro ao criar diretório {directory}: {e}")
                    messagebox.showerror(
                        "Erro",
                        f"Não foi possível criar o diretório '{directory}'.\n\n"
                        f"Erro: {str(e)}"
                    )
    
    def on_tab_selected(self):
        """Método chamado quando a aba é selecionada."""
        self.main_window.set_status("Configurações do Sistema")
        
        # Recarrega as configurações
        self.load_config()
