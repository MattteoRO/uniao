# -*- coding: utf-8 -*-

"""
Aba Mecânico
Permite cadastrar, editar e remover mecânicos, além de gerenciar suas carteiras digitais.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import datetime

from models import Mecanico, Carteira
from services.carteira_service import CarteiraService
from utils.formatters import format_currency, format_date

logger = logging.getLogger(__name__)

class MecanicoTab(ttk.Frame):
    """
    Classe que representa a aba Mecânico, onde é possível gerenciar mecânicos e suas carteiras.
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.carteira_service = CarteiraService()
        self.setup_ui()
        logger.debug("Aba Mecânico inicializada")
    
    def setup_ui(self):
        """Configura a interface da aba Mecânico."""
        # Container principal com scroll
        self.main_canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.bind("<Configure>", lambda e: self.main_canvas.itemconfig(
            self.main_canvas.find_withtag("win")[0], width=e.width
        ))
        
        # Container principal
        self.main_container = ttk.Frame(self.scrollable_frame)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Notebook para subabas
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Subaba de Mecânicos
        self.mecanicos_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mecanicos_frame, text="Mecânicos")
        
        # Subaba de Carteiras
        self.carteiras_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.carteiras_frame, text="Carteiras Digitais")
        
        # Configura as subabas
        self.setup_mecanicos_tab()
        self.setup_carteiras_tab()
    
    def setup_mecanicos_tab(self):
        """Configura a subaba de Mecânicos."""
        # Container principal
        main_frame = ttk.Frame(self.mecanicos_frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Gerenciamento de Mecânicos",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Frame para lista de mecânicos
        list_frame = ttk.LabelFrame(main_frame, text="Mecânicos Cadastrados")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Treeview para lista de mecânicos
        self.mecanicos_tree = ttk.Treeview(
            list_frame, 
            columns=("id", "nome", "data_cadastro"),
            show="headings",
            height=10
        )
        
        # Configuração das colunas
        self.mecanicos_tree.heading("id", text="ID")
        self.mecanicos_tree.heading("nome", text="Nome")
        self.mecanicos_tree.heading("data_cadastro", text="Data de Cadastro")
        
        self.mecanicos_tree.column("id", width=50, anchor=tk.CENTER)
        self.mecanicos_tree.column("nome", width=300)
        self.mecanicos_tree.column("data_cadastro", width=150, anchor=tk.CENTER)
        
        # Scrollbar para lista de mecânicos
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.mecanicos_tree.yview)
        self.mecanicos_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mecanicos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click para editar mecânico
        self.mecanicos_tree.bind("<Double-1>", lambda e: self.edit_mecanico())
        
        # Frame para botões de ação
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Botão para novo mecânico
        self.btn_novo = ttk.Button(
            buttons_frame,
            text="Novo Mecânico",
            command=self.new_mecanico
        )
        self.btn_novo.pack(side=tk.LEFT, padx=5)
        
        # Botão para editar mecânico
        self.btn_editar = ttk.Button(
            buttons_frame,
            text="Editar Mecânico",
            command=self.edit_mecanico
        )
        self.btn_editar.pack(side=tk.LEFT, padx=5)
        
        # Botão para remover mecânico
        self.btn_remover = ttk.Button(
            buttons_frame,
            text="Desativar Mecânico",
            command=self.deactivate_mecanico
        )
        self.btn_remover.pack(side=tk.RIGHT, padx=5)
    
    def setup_carteiras_tab(self):
        """Configura a subaba de Carteiras Digitais."""
        # Container principal
        main_frame = ttk.Frame(self.carteiras_frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Carteiras Digitais",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Frame para seleção de carteira
        selection_frame = ttk.LabelFrame(main_frame, text="Selecionar Carteira")
        selection_frame.pack(fill=tk.X, pady=10)
        
        # Combobox para seleção de carteira
        ttk.Label(selection_frame, text="Carteira:").pack(side=tk.LEFT, padx=5, pady=10)
        
        self.carteira_var = tk.StringVar()
        self.carteiras_combobox = ttk.Combobox(
            selection_frame, 
            width=40, 
            textvariable=self.carteira_var,
            state="readonly"
        )
        self.carteiras_combobox.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Botão para carregar carteira
        ttk.Button(
            selection_frame,
            text="Carregar Carteira",
            command=self.load_carteira
        ).pack(side=tk.LEFT, padx=5, pady=10)
        
        # Frame para informações da carteira
        self.carteira_info_frame = ttk.LabelFrame(main_frame, text="Informações da Carteira")
        self.carteira_info_frame.pack(fill=tk.X, pady=10)
        
        # Informações da carteira
        info_frame = ttk.Frame(self.carteira_info_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Nome/Tipo
        ttk.Label(info_frame, text="Nome/Tipo:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.carteira_nome_label = ttk.Label(info_frame, text="-")
        self.carteira_nome_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # ID
        ttk.Label(info_frame, text="ID:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.carteira_id_label = ttk.Label(info_frame, text="-")
        self.carteira_id_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Saldo
        ttk.Label(info_frame, text="Saldo Atual:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.carteira_saldo_label = ttk.Label(info_frame, text="R$ 0,00", font=('Arial', 11, 'bold'))
        self.carteira_saldo_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Frame para extrato
        self.extrato_frame = ttk.LabelFrame(main_frame, text="Extrato de Movimentações")
        self.extrato_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Treeview para extrato
        self.extrato_tree = ttk.Treeview(
            self.extrato_frame, 
            columns=("data", "valor", "justificativa"),
            show="headings",
            height=10
        )
        
        # Configuração das colunas
        self.extrato_tree.heading("data", text="Data")
        self.extrato_tree.heading("valor", text="Valor")
        self.extrato_tree.heading("justificativa", text="Justificativa")
        
        self.extrato_tree.column("data", width=150, anchor=tk.CENTER)
        self.extrato_tree.column("valor", width=100, anchor=tk.CENTER)
        self.extrato_tree.column("justificativa", width=400)
        
        # Scrollbar para extrato
        scrollbar = ttk.Scrollbar(self.extrato_frame, orient=tk.VERTICAL, command=self.extrato_tree.yview)
        self.extrato_tree.configure(yscrollcommand=scrollbar.set)
        
        self.extrato_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para filtros
        filters_frame = ttk.Frame(main_frame)
        filters_frame.pack(fill=tk.X, pady=5)
        
        # Filtro por data
        ttk.Label(filters_frame, text="Filtrar por Data:").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filters_frame, text="De:").pack(side=tk.LEFT, padx=5)
        self.data_inicio_var = tk.StringVar()
        ttk.Entry(filters_frame, width=10, textvariable=self.data_inicio_var).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(filters_frame, text="Até:").pack(side=tk.LEFT, padx=5)
        self.data_fim_var = tk.StringVar()
        ttk.Entry(filters_frame, width=10, textvariable=self.data_fim_var).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            filters_frame,
            text="Filtrar",
            command=self.filter_extrato
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            filters_frame,
            text="Limpar Filtros",
            command=self.clear_filters
        ).pack(side=tk.LEFT, padx=5)
        
        # Frame para botões de ação
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Botão para registrar movimentação
        self.btn_movimentacao = ttk.Button(
            buttons_frame,
            text="Registrar Movimentação",
            command=self.register_movimentacao
        )
        self.btn_movimentacao.pack(side=tk.LEFT, padx=5)
        
        # Inicialmente desabilita os botões de movimentação
        self.btn_movimentacao.config(state=tk.DISABLED)
    
    def load_mecanicos(self):
        """Carrega os mecânicos do banco de dados para a treeview."""
        # Limpa a lista atual
        for item in self.mecanicos_tree.get_children():
            self.mecanicos_tree.delete(item)
        
        # Carrega os mecânicos
        mecanicos = Mecanico.get_all()
        
        # Adiciona à treeview
        for mecanico in mecanicos:
            # Formata a data
            data_formatada = format_date(mecanico['data_cadastro'])
            
            self.mecanicos_tree.insert(
                "", 
                tk.END, 
                values=(
                    mecanico['id'],
                    mecanico['nome'],
                    data_formatada
                )
            )
    
    def load_carteiras(self):
        """Carrega as carteiras do banco de dados para o combobox."""
        # Carrega mecânicos e carteira da loja
        mecanicos = Mecanico.get_all()
        carteira_loja = Carteira.get_loja_carteira()
        
        # Lista de carteiras
        carteiras = []
        
        # Adiciona carteira da loja
        if carteira_loja:
            carteiras.append(f"Loja (ID: {carteira_loja['id']})")
        
        # Adiciona carteiras dos mecânicos
        for mecanico in mecanicos:
            carteira = Carteira.get_by_mecanico(mecanico['id'])
            if carteira:
                carteiras.append(f"{mecanico['nome']} (ID: {carteira['id']})")
        
        # Atualiza o combobox
        self.carteiras_combobox['values'] = carteiras
        
        # Seleciona a primeira carteira, se houver
        if carteiras:
            self.carteiras_combobox.current(0)
    
    def new_mecanico(self):
        """Exibe o diálogo para cadastrar um novo mecânico."""
        # Cria uma janela de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Novo Mecânico")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Container principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campo de nome
        ttk.Label(main_frame, text="Nome do Mecânico:").grid(row=0, column=0, padx=5, pady=10)
        
        nome_var = tk.StringVar()
        nome_entry = ttk.Entry(main_frame, width=30, textvariable=nome_var)
        nome_entry.grid(row=0, column=1, padx=5, pady=10)
        
        # Frame para botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Botão de cancelar
        ttk.Button(
            buttons_frame, 
            text="Cancelar", 
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão de confirmar
        def confirm_add():
            try:
                nome = nome_var.get().strip()
                
                if not nome:
                    messagebox.showerror("Erro", "O nome do mecânico é obrigatório.")
                    return
                
                # Cria e salva o novo mecânico
                mecanico = Mecanico(nome=nome)
                mecanico.save()
                
                messagebox.showinfo("Sucesso", f"Mecânico '{nome}' cadastrado com sucesso!")
                
                # Atualiza a lista
                self.load_mecanicos()
                self.load_carteiras()
                
                dialog.destroy()
                
            except Exception as e:
                logger.error(f"Erro ao cadastrar mecânico: {e}")
                messagebox.showerror("Erro", f"Erro ao cadastrar mecânico: {str(e)}")
        
        ttk.Button(
            buttons_frame, 
            text="Confirmar", 
            command=confirm_add
        ).pack(side=tk.RIGHT, padx=5)
        
        # Foco inicial no campo de nome
        nome_entry.focus_set()
    
    def edit_mecanico(self):
        """Exibe o diálogo para editar um mecânico."""
        selection = self.mecanicos_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione um mecânico para editar.")
            return
        
        # Obtém os dados do mecânico selecionado
        item = self.mecanicos_tree.item(selection[0])
        mecanico_data = item['values']
        
        # Carrega o mecânico do banco de dados
        mecanico = Mecanico.get_by_id(mecanico_data[0])
        
        if not mecanico:
            messagebox.showerror("Erro", "Mecânico não encontrado no banco de dados.")
            return
        
        # Cria uma janela de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Editar Mecânico #{mecanico['id']}")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Container principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campo de nome
        ttk.Label(main_frame, text="Nome do Mecânico:").grid(row=0, column=0, padx=5, pady=10)
        
        nome_var = tk.StringVar(value=mecanico['nome'])
        nome_entry = ttk.Entry(main_frame, width=30, textvariable=nome_var)
        nome_entry.grid(row=0, column=1, padx=5, pady=10)
        
        # Frame para botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Botão de cancelar
        ttk.Button(
            buttons_frame, 
            text="Cancelar", 
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão de confirmar
        def confirm_edit():
            try:
                nome = nome_var.get().strip()
                
                if not nome:
                    messagebox.showerror("Erro", "O nome do mecânico é obrigatório.")
                    return
                
                # Atualiza e salva o mecânico
                mecanico_obj = Mecanico(
                    id=mecanico['id'],
                    nome=nome,
                    data_cadastro=mecanico['data_cadastro'],
                    ativo=mecanico['ativo']
                )
                mecanico_obj.save()
                
                messagebox.showinfo("Sucesso", f"Mecânico #{mecanico['id']} atualizado com sucesso!")
                
                # Atualiza a lista
                self.load_mecanicos()
                self.load_carteiras()
                
                dialog.destroy()
                
            except Exception as e:
                logger.error(f"Erro ao atualizar mecânico: {e}")
                messagebox.showerror("Erro", f"Erro ao atualizar mecânico: {str(e)}")
        
        ttk.Button(
            buttons_frame, 
            text="Confirmar", 
            command=confirm_edit
        ).pack(side=tk.RIGHT, padx=5)
        
        # Foco inicial no campo de nome
        nome_entry.focus_set()
    
    def deactivate_mecanico(self):
        """Desativa um mecânico (exclusão lógica)."""
        selection = self.mecanicos_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione um mecânico para desativar.")
            return
        
        # Obtém os dados do mecânico selecionado
        item = self.mecanicos_tree.item(selection[0])
        mecanico_data = item['values']
        
        # Confirmação
        if not messagebox.askyesno(
            "Confirmar Desativação",
            f"Deseja realmente desativar o mecânico '{mecanico_data[1]}'?\n\n"
            "Isso não excluirá seus dados históricos, mas o mecânico não poderá "
            "mais ser selecionado para novos serviços."
        ):
            return
        
        try:
            # Carrega o mecânico do banco de dados
            mecanico = Mecanico.get_by_id(mecanico_data[0])
            
            if not mecanico:
                messagebox.showerror("Erro", "Mecânico não encontrado no banco de dados.")
                return
            
            # Desativa o mecânico
            mecanico_obj = Mecanico(
                id=mecanico['id'],
                nome=mecanico['nome'],
                data_cadastro=mecanico['data_cadastro'],
                ativo=0  # Desativa
            )
            mecanico_obj.save()
            
            messagebox.showinfo("Sucesso", f"Mecânico '{mecanico['nome']}' desativado com sucesso!")
            
            # Atualiza a lista
            self.load_mecanicos()
            
        except Exception as e:
            logger.error(f"Erro ao desativar mecânico: {e}")
            messagebox.showerror("Erro", f"Erro ao desativar mecânico: {str(e)}")
    
    def load_carteira(self):
        """Carrega a carteira selecionada."""
        carteira_str = self.carteira_var.get()
        
        if not carteira_str:
            messagebox.showinfo("Seleção", "Selecione uma carteira para carregar.")
            return
        
        # Extrai o ID da carteira
        try:
            carteira_id = int(carteira_str.split("ID: ")[1].strip(")"))
        except (IndexError, ValueError):
            messagebox.showerror("Erro", "Formato inválido de ID da carteira.")
            return
        
        try:
            # Carrega a carteira
            carteira = Carteira.get_by_id(carteira_id)
            
            if not carteira:
                messagebox.showerror("Erro", "Carteira não encontrada no banco de dados.")
                return
            
            # Atualiza informações na interface
            if carteira['tipo'] == 'loja':
                self.carteira_nome_label.config(text="Loja")
            else:
                mecanico = Mecanico.get_by_id(carteira['mecanico_id'])
                self.carteira_nome_label.config(text=mecanico['nome'] if mecanico else "-")
            
            self.carteira_id_label.config(text=str(carteira['id']))
            self.carteira_saldo_label.config(text=format_currency(carteira['saldo']))
            
            # Carrega o extrato
            self.load_extrato(carteira['id'])
            
            # Habilita botão de movimentação
            self.btn_movimentacao.config(state=tk.NORMAL)
            
        except Exception as e:
            logger.error(f"Erro ao carregar carteira: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar carteira: {str(e)}")
    
    def load_extrato(self, carteira_id, data_inicio=None, data_fim=None):
        """
        Carrega o extrato de uma carteira.
        
        Args:
            carteira_id (int): ID da carteira
            data_inicio (str): Data inicial para filtro (formato: YYYY-MM-DD)
            data_fim (str): Data final para filtro (formato: YYYY-MM-DD)
        """
        # Limpa o extrato atual
        for item in self.extrato_tree.get_children():
            self.extrato_tree.delete(item)
        
        try:
            # Carrega a carteira
            carteira = Carteira.get_by_id(carteira_id)
            
            if not carteira:
                return
            
            # Cria objeto carteira
            carteira_obj = Carteira(**dict(carteira))
            
            # Carrega movimentações
            movimentacoes = carteira_obj.get_extrato(data_inicio, data_fim)
            
            # Adiciona à treeview
            for mov in movimentacoes:
                # Formata a data
                data_formatada = format_date(mov['data'])
                
                # Define a cor com base no valor (positivo ou negativo)
                tag = "positivo" if mov['valor'] >= 0 else "negativo"
                
                self.extrato_tree.insert(
                    "", 
                    tk.END, 
                    values=(
                        data_formatada,
                        format_currency(mov['valor']),
                        mov['justificativa'] or ""
                    ),
                    tags=(tag,)
                )
            
            # Configura as cores
            self.extrato_tree.tag_configure("positivo", foreground="green")
            self.extrato_tree.tag_configure("negativo", foreground="red")
            
        except Exception as e:
            logger.error(f"Erro ao carregar extrato: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar extrato: {str(e)}")
    
    def filter_extrato(self):
        """Filtra o extrato por data."""
        carteira_str = self.carteira_var.get()
        
        if not carteira_str:
            messagebox.showinfo("Seleção", "Selecione uma carteira primeiro.")
            return
        
        # Extrai o ID da carteira
        try:
            carteira_id = int(carteira_str.split("ID: ")[1].strip(")"))
        except (IndexError, ValueError):
            messagebox.showerror("Erro", "Formato inválido de ID da carteira.")
            return
        
        # Obtém as datas do filtro
        data_inicio = self.data_inicio_var.get().strip()
        data_fim = self.data_fim_var.get().strip()
        
        # Valida formato das datas (YYYY-MM-DD)
        if data_inicio and not self._validate_date_format(data_inicio):
            messagebox.showerror("Erro", "Formato de data inicial inválido. Use YYYY-MM-DD.")
            return
        
        if data_fim and not self._validate_date_format(data_fim):
            messagebox.showerror("Erro", "Formato de data final inválido. Use YYYY-MM-DD.")
            return
        
        # Carrega o extrato filtrado
        self.load_extrato(carteira_id, data_inicio, data_fim)
    
    def clear_filters(self):
        """Limpa os filtros de data e recarrega o extrato."""
        self.data_inicio_var.set("")
        self.data_fim_var.set("")
        
        # Recarrega o extrato sem filtros
        carteira_str = self.carteira_var.get()
        
        if carteira_str:
            try:
                carteira_id = int(carteira_str.split("ID: ")[1].strip(")"))
                self.load_extrato(carteira_id)
            except (IndexError, ValueError):
                pass
    
    def register_movimentacao(self):
        """Exibe o diálogo para registrar uma nova movimentação."""
        carteira_str = self.carteira_var.get()
        
        if not carteira_str:
            messagebox.showinfo("Seleção", "Selecione uma carteira primeiro.")
            return
        
        # Extrai o ID da carteira
        try:
            carteira_id = int(carteira_str.split("ID: ")[1].strip(")"))
        except (IndexError, ValueError):
            messagebox.showerror("Erro", "Formato inválido de ID da carteira.")
            return
        
        # Carrega a carteira
        carteira = Carteira.get_by_id(carteira_id)
        
        if not carteira:
            messagebox.showerror("Erro", "Carteira não encontrada no banco de dados.")
            return
        
        # Cria uma janela de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Registrar Movimentação")
        dialog.geometry("500x250")
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Container principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tipo de Carteira
        ttk.Label(main_frame, text="Carteira:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        if carteira['tipo'] == 'loja':
            carteira_nome = "Loja"
        else:
            mecanico = Mecanico.get_by_id(carteira['mecanico_id'])
            carteira_nome = mecanico['nome'] if mecanico else "-"
        
        ttk.Label(main_frame, text=carteira_nome).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Saldo Atual
        ttk.Label(main_frame, text="Saldo Atual:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(main_frame, text=format_currency(carteira['saldo'])).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Valor
        ttk.Label(main_frame, text="Valor:*").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        valor_var = tk.StringVar()
        valor_entry = ttk.Entry(main_frame, width=15, textvariable=valor_var)
        valor_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(
            main_frame, 
            text="(Use valores negativos para saques/retiradas)",
            font=('Arial', 8)
        ).grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Justificativa
        ttk.Label(main_frame, text="Justificativa:*").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        justificativa_var = tk.StringVar()
        justificativa_entry = ttk.Entry(main_frame, width=40, textvariable=justificativa_var)
        justificativa_entry.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Frame para botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        # Botão de cancelar
        ttk.Button(
            buttons_frame, 
            text="Cancelar", 
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão de confirmar
        def confirm_register():
            try:
                # Validação do valor
                valor_str = valor_var.get().strip()
                justificativa = justificativa_var.get().strip()
                
                try:
                    valor = float(valor_str)
                except ValueError:
                    messagebox.showerror("Erro", "O valor deve ser um número válido.")
                    return
                
                # Justificativa obrigatória para saídas
                if valor < 0 and not justificativa:
                    messagebox.showerror("Erro", "A justificativa é obrigatória para retiradas de valor.")
                    return
                
                # Confirma retiradas
                if valor < 0 and not messagebox.askyesno(
                    "Confirmar Retirada",
                    f"Confirma a retirada de {format_currency(abs(valor))} da carteira de {carteira_nome}?"
                ):
                    return
                
                # Registra a movimentação
                carteira_obj = Carteira(**dict(carteira))
                carteira_obj.adicionar_movimentacao(valor, justificativa)
                
                messagebox.showinfo("Sucesso", "Movimentação registrada com sucesso!")
                
                # Atualiza a interface
                self.load_carteira()
                
                dialog.destroy()
                
            except Exception as e:
                logger.error(f"Erro ao registrar movimentação: {e}")
                messagebox.showerror("Erro", f"Erro ao registrar movimentação: {str(e)}")
        
        ttk.Button(
            buttons_frame, 
            text="Confirmar", 
            command=confirm_register
        ).pack(side=tk.RIGHT, padx=5)
        
        # Foco inicial no campo de valor
        valor_entry.focus_set()
    
    def _validate_date_format(self, date_str):
        """
        Valida o formato de uma data.
        
        Args:
            date_str (str): String de data para validar
            
        Returns:
            bool: True se o formato for válido, False caso contrário
        """
        import re
        
        # Padrão YYYY-MM-DD
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        
        if not re.match(pattern, date_str):
            return False
        
        # Valida se é uma data válida
        try:
            year, month, day = map(int, date_str.split('-'))
            datetime.datetime(year, month, day)
            return True
        except ValueError:
            return False
    
    def on_navigate(self, show_carteiras=False):
        """
        Método chamado quando o usuário navega para esta aba.
        
        Args:
            show_carteiras (bool): Se True, exibe a subaba de carteiras
        """
        # Carrega os dados
        self.load_mecanicos()
        self.load_carteiras()
        
        # Se solicitado, exibe a subaba de carteiras
        if show_carteiras:
            self.notebook.select(1)  # Índice 1 = Carteiras
    
    def on_tab_selected(self):
        """Método chamado quando a aba é selecionada."""
        self.main_window.set_status("Gerenciamento de Mecânicos")
        
        # Carrega os dados ao selecionar a aba
        self.load_mecanicos()
        self.load_carteiras()
