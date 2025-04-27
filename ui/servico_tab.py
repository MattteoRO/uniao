# -*- coding: utf-8 -*-

"""
Aba Serviço
Permite cadastrar novos serviços, gerenciar peças e gerar relatórios.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import re
import datetime

from models import Mecanico, Servico
from services.csv_manager import CSVManager
from services.pdf_generator import generate_pdf_cliente, generate_pdf_mecanico, generate_pdf_loja
from utils.validators import validate_phone, validate_percentage, validate_money
from utils.formatters import format_currency, format_phone

logger = logging.getLogger(__name__)

class ServicoTab(ttk.Frame):
    """
    Classe que representa a aba Serviço, onde é possível cadastrar novos serviços.
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.servico = None
        self.csv_manager = CSVManager()
        self.setup_ui()
        logger.debug("Aba Serviço inicializada")
    
    def setup_ui(self):
        """Configura a interface da aba Serviço."""
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
        
        # Título
        self.title_label = ttk.Label(
            self.main_container,
            text="Novo Serviço",
            font=('Arial', 16, 'bold')
        )
        self.title_label.pack(pady=(0, 20))
        
        # Duas colunas principais
        self.columns_frame = ttk.Frame(self.main_container)
        self.columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # Coluna da esquerda - Informações do serviço
        self.left_frame = ttk.LabelFrame(self.columns_frame, text="Informações do Serviço")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        # Campos de serviço
        self.create_service_form()
        
        # Coluna da direita - Peças do serviço
        self.right_frame = ttk.LabelFrame(self.columns_frame, text="Peças do Serviço")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        
        # Campos de peças
        self.create_parts_form()
        
        # Resumo e botões de ação
        self.summary_frame = ttk.LabelFrame(self.main_container, text="Resumo do Serviço")
        self.summary_frame.pack(fill=tk.X, pady=(20, 10))
        
        # Valores totais
        self.summary_values_frame = ttk.Frame(self.summary_frame)
        self.summary_values_frame.pack(fill=tk.X, expand=True, padx=10, pady=10)
        
        # Valor do serviço
        ttk.Label(self.summary_values_frame, text="Valor da Mão de Obra:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.summary_service_value = ttk.Label(self.summary_values_frame, text="R$ 0,00")
        self.summary_service_value.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Valor das peças
        ttk.Label(self.summary_values_frame, text="Valor das Peças:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.summary_parts_value = ttk.Label(self.summary_values_frame, text="R$ 0,00")
        self.summary_parts_value.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Valor total
        ttk.Label(
            self.summary_values_frame, 
            text="VALOR TOTAL:", 
            font=('Arial', 11, 'bold')
        ).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.summary_total_value = ttk.Label(
            self.summary_values_frame, 
            text="R$ 0,00", 
            font=('Arial', 11, 'bold')
        )
        self.summary_total_value.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Separador
        ttk.Separator(self.main_container, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Frame para botões de relatório
        self.report_frame = ttk.Frame(self.main_container)
        self.report_frame.pack(fill=tk.X, pady=5)
        
        # Tipo de relatório
        ttk.Label(self.report_frame, text="Tipo de Relatório:").pack(side=tk.LEFT, padx=5)
        self.report_type = tk.StringVar(value="cliente")
        
        report_type_cbx = ttk.Combobox(
            self.report_frame, 
            textvariable=self.report_type,
            values=["cliente", "mecanico", "loja"],
            state="readonly",
            width=15
        )
        report_type_cbx.pack(side=tk.LEFT, padx=5)
        
        # Botão de gerar PDF
        self.btn_gerar_pdf = ttk.Button(
            self.report_frame,
            text="Gerar PDF",
            command=self.generate_pdf
        )
        self.btn_gerar_pdf.pack(side=tk.LEFT, padx=5)
        
        # Frame para botões de ação
        self.action_buttons_frame = ttk.Frame(self.main_container)
        self.action_buttons_frame.pack(fill=tk.X, pady=10)
        
        # Botão de cancelar
        self.btn_cancelar = ttk.Button(
            self.action_buttons_frame,
            text="Cancelar",
            command=self.cancel_service
        )
        self.btn_cancelar.pack(side=tk.LEFT, padx=5)
        
        # Botão de salvar
        self.btn_salvar = ttk.Button(
            self.action_buttons_frame,
            text="Salvar Serviço",
            command=self.save_service
        )
        self.btn_salvar.pack(side=tk.RIGHT, padx=5)
        
        # Inicializa um serviço vazio
        self.new_service()
    
    def create_service_form(self):
        """Cria o formulário de cadastro de serviço."""
        form_frame = ttk.Frame(self.left_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Cliente
        ttk.Label(form_frame, text="Cliente:*").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.cliente_var = tk.StringVar()
        cliente_entry = ttk.Entry(form_frame, width=30, textvariable=self.cliente_var)
        cliente_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Telefone
        ttk.Label(form_frame, text="Telefone:*").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.telefone_var = tk.StringVar()
        telefone_entry = ttk.Entry(form_frame, width=30, textvariable=self.telefone_var)
        telefone_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Validação do campo de telefone
        self.telefone_var.trace_add("write", self.validate_telefone)
        
        # Descrição da Mão de Obra
        ttk.Label(form_frame, text="Descrição da Mão de Obra:*").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.descricao_var = tk.StringVar()
        self.descricao_text = tk.Text(form_frame, width=30, height=5)
        self.descricao_text.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Limite de caracteres (500) e conversão para maiúsculas
        self.descricao_text.bind("<KeyRelease>", self.on_descricao_change)
        
        # Contador de caracteres
        self.char_count_var = tk.StringVar(value="0/500 caracteres")
        ttk.Label(form_frame, textvariable=self.char_count_var).grid(row=3, column=1, sticky=tk.E, padx=5)
        
        # Mecânico
        ttk.Label(form_frame, text="Mecânico Responsável:*").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.mecanico_var = tk.StringVar()
        self.mecanico_combobox = ttk.Combobox(form_frame, width=28, textvariable=self.mecanico_var, state="readonly")
        self.mecanico_combobox.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Valor do Serviço
        ttk.Label(form_frame, text="Valor do Serviço:*").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.valor_servico_var = tk.StringVar(value="0.00")
        valor_servico_entry = ttk.Entry(form_frame, width=15, textvariable=self.valor_servico_var)
        valor_servico_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Focus e seleção ao clicar no campo de valor
        valor_servico_entry.bind("<FocusIn>", lambda e: valor_servico_entry.selection_range(0, tk.END))
        
        # Validação do campo de valor
        self.valor_servico_var.trace_add("write", self.validate_valor_servico)
        
        # Porcentagem do mecânico
        ttk.Label(form_frame, text="Porcentagem do Mecânico:*").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Frame para o campo de porcentagem
        porcentagem_frame = ttk.Frame(form_frame)
        porcentagem_frame.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.porcentagem_var = tk.StringVar(value="0")
        porcentagem_entry = ttk.Entry(porcentagem_frame, width=5, textvariable=self.porcentagem_var)
        porcentagem_entry.pack(side=tk.LEFT)
        
        ttk.Label(porcentagem_frame, text="%").pack(side=tk.LEFT)
        
        # Validação do campo de porcentagem
        self.porcentagem_var.trace_add("write", self.validate_porcentagem)
        
        # Carregar mecânicos
        self.load_mecanicos()
    
    def create_parts_form(self):
        """Cria o formulário de pesquisa e adição de peças."""
        # Frame de pesquisa
        search_frame = ttk.Frame(self.right_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Pesquisar Peça:").pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, width=25, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = ttk.Button(search_frame, text="Buscar", command=self.search_parts)
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter para pesquisar
        search_entry.bind("<Return>", lambda e: self.search_parts())
        
        # Frame de resultados
        results_frame = ttk.LabelFrame(self.right_frame, text="Resultados da Pesquisa")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview para resultados
        self.results_tree = ttk.Treeview(
            results_frame, 
            columns=("id", "descricao", "preco", "codigo"),
            show="headings",
            height=5
        )
        
        # Configuração das colunas
        self.results_tree.heading("id", text="ID")
        self.results_tree.heading("descricao", text="Descrição")
        self.results_tree.heading("preco", text="Preço")
        self.results_tree.heading("codigo", text="Código de Barras")
        
        self.results_tree.column("id", width=50, anchor=tk.CENTER)
        self.results_tree.column("descricao", width=200)
        self.results_tree.column("preco", width=80, anchor=tk.CENTER)
        self.results_tree.column("codigo", width=120, anchor=tk.CENTER)
        
        # Scrollbar para resultados
        results_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click para adicionar peça
        self.results_tree.bind("<Double-1>", lambda e: self.show_add_part_dialog())
        
        # Frame para lista de peças adicionadas
        added_frame = ttk.LabelFrame(self.right_frame, text="Peças Adicionadas")
        added_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview para peças adicionadas
        self.added_tree = ttk.Treeview(
            added_frame, 
            columns=("descricao", "quantidade", "preco", "total"),
            show="headings",
            height=5
        )
        
        # Configuração das colunas
        self.added_tree.heading("descricao", text="Descrição")
        self.added_tree.heading("quantidade", text="Qtd")
        self.added_tree.heading("preco", text="Preço Unit.")
        self.added_tree.heading("total", text="Total")
        
        self.added_tree.column("descricao", width=200)
        self.added_tree.column("quantidade", width=50, anchor=tk.CENTER)
        self.added_tree.column("preco", width=100, anchor=tk.CENTER)
        self.added_tree.column("total", width=100, anchor=tk.CENTER)
        
        # Scrollbar para peças adicionadas
        added_scrollbar = ttk.Scrollbar(added_frame, orient=tk.VERTICAL, command=self.added_tree.yview)
        self.added_tree.configure(yscrollcommand=added_scrollbar.set)
        
        self.added_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        added_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botões para gerenciar peças
        buttons_frame = ttk.Frame(self.right_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        add_button = ttk.Button(
            buttons_frame, 
            text="Adicionar Peça Selecionada", 
            command=self.show_add_part_dialog
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        remove_button = ttk.Button(
            buttons_frame, 
            text="Remover Peça Selecionada", 
            command=self.remove_part
        )
        remove_button.pack(side=tk.RIGHT, padx=5)
        
        # Double-click para editar quantidade
        self.added_tree.bind("<Double-1>", lambda e: self.edit_part_quantity())
    
    def on_descricao_change(self, event):
        """Callback para limitação de caracteres e conversão para maiúsculas."""
        # Obtém o texto atual
        text = self.descricao_text.get("1.0", tk.END)
        
        # Limita a 500 caracteres
        if len(text) > 501:  # 501 porque o tk.END adiciona uma quebra de linha
            text = text[:500]
            self.descricao_text.delete("1.0", tk.END)
            self.descricao_text.insert("1.0", text)
        
        # Converte para maiúsculas
        uppercase_text = text.upper()
        if text != uppercase_text:
            current_pos = self.descricao_text.index(tk.INSERT)
            self.descricao_text.delete("1.0", tk.END)
            self.descricao_text.insert("1.0", uppercase_text)
            try:
                self.descricao_text.mark_set(tk.INSERT, current_pos)
            except tk.TclError:
                pass  # Ignora erros de posição inválida
        
        # Atualiza contador
        self.char_count_var.set(f"{len(text.strip())}/500 caracteres")
    
    def validate_telefone(self, *args):
        """Valida o campo de telefone."""
        telefone = self.telefone_var.get()
        valid, msg = validate_phone(telefone)
        
        if not valid and telefone:
            self.telefone_var.set(re.sub(r'[^0-9]', '', telefone))
    
    def validate_valor_servico(self, *args):
        """Valida o campo de valor do serviço."""
        valor = self.valor_servico_var.get()
        valid, msg = validate_money(valor)
        
        if not valid and valor:
            # Mantém apenas dígitos e ponto
            cleaned = re.sub(r'[^0-9.]', '', valor)
            # Remove pontos extras
            if cleaned.count('.') > 1:
                parts = cleaned.split('.')
                cleaned = parts[0] + '.' + ''.join(parts[1:])
            
            self.valor_servico_var.set(cleaned)
        
        # Atualiza o resumo
        self.update_summary()
    
    def validate_porcentagem(self, *args):
        """Valida o campo de porcentagem do mecânico."""
        porcentagem = self.porcentagem_var.get()
        valid, msg = validate_percentage(porcentagem)
        
        if not valid and porcentagem:
            # Mantém apenas dígitos
            cleaned = re.sub(r'[^0-9]', '', porcentagem)
            # Limita ao valor máximo de 100
            try:
                if int(cleaned) > 100:
                    cleaned = "100"
            except ValueError:
                cleaned = "0"
            
            self.porcentagem_var.set(cleaned)
    
    def load_mecanicos(self):
        """Carrega os mecânicos do banco de dados para o combobox."""
        mecanicos = Mecanico.get_all()
        
        if not mecanicos:
            messagebox.showwarning(
                "Nenhum Mecânico",
                "Não há mecânicos cadastrados. Você deve cadastrar pelo menos um mecânico antes de criar um serviço."
            )
            self.main_window.navigate_to("mecanico")
            return
        
        # Preenche o combobox
        mecanicos_list = [f"{m['nome']} (ID: {m['id']})" for m in mecanicos]
        self.mecanico_combobox['values'] = mecanicos_list
        
        # Se houver apenas um mecânico, seleciona automaticamente
        if len(mecanicos_list) == 1:
            self.mecanico_combobox.current(0)
    
    def search_parts(self):
        """Pesquisa peças no arquivo CSV."""
        search_term = self.search_var.get().strip()
        
        if not search_term:
            messagebox.showinfo("Pesquisa Vazia", "Digite um termo para pesquisar.")
            return
        
        # Limpa resultados anteriores
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        try:
            # Busca no CSV
            results = self.csv_manager.search_parts(search_term)
            
            if not results:
                messagebox.showinfo("Sem Resultados", "Nenhuma peça encontrada com esse termo.")
                return
            
            # Preenche a treeview com os resultados
            for part in results:
                self.results_tree.insert(
                    "", 
                    tk.END, 
                    values=(
                        part['ID'],
                        part['DESCRICAO'],
                        part['PRECOVENDA'],
                        part['CODBARRAS'] if part['CODBARRAS'] != 'NULL' else ''
                    )
                )
            
            # Seleciona o primeiro resultado
            if self.results_tree.get_children():
                self.results_tree.selection_set(self.results_tree.get_children()[0])
                self.results_tree.focus(self.results_tree.get_children()[0])
                
        except Exception as e:
            logger.error(f"Erro ao pesquisar peças: {e}")
            messagebox.showerror("Erro", f"Erro ao pesquisar peças: {str(e)}")
    
    def show_add_part_dialog(self):
        """Exibe o diálogo para adicionar uma peça ao serviço."""
        selection = self.results_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione uma peça para adicionar.")
            return
        
        # Obtém os dados da peça selecionada
        item = self.results_tree.item(selection[0])
        part_data = item['values']
        
        # Cria uma janela de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Adicionar Peça")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Container principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Informações da peça
        ttk.Label(main_frame, text="Descrição:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(main_frame, text=part_data[1], wraplength=300).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(main_frame, text="Preço Original:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(main_frame, text=part_data[2]).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Quantidade
        ttk.Label(main_frame, text="Quantidade:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        quantidade_var = tk.StringVar(value="1")
        quantidade_entry = ttk.Entry(main_frame, width=10, textvariable=quantidade_var)
        quantidade_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Preço customizado
        ttk.Label(main_frame, text="Preço Customizado:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Converter preço de string para float
        preco_original = part_data[2].replace(".", "").replace(",", ".")
        try:
            preco_original = float(preco_original)
        except ValueError:
            preco_original = 0.0
        
        preco_var = tk.StringVar(value=f"{preco_original:.2f}")
        preco_entry = ttk.Entry(main_frame, width=15, textvariable=preco_var)
        preco_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Checkbox para atualizar CSV
        atualizar_csv_var = tk.BooleanVar(value=False)
        atualizar_csv_check = ttk.Checkbutton(
            main_frame, 
            text="Atualizar preço no CSV", 
            variable=atualizar_csv_var
        )
        atualizar_csv_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Frame para botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Botão de cancelar
        ttk.Button(
            buttons_frame, 
            text="Cancelar", 
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão de confirmar
        def confirm_add():
            try:
                # Validação da quantidade
                quantidade = quantidade_var.get()
                try:
                    quantidade = int(quantidade)
                    if quantidade <= 0:
                        raise ValueError("A quantidade deve ser maior que zero.")
                except ValueError:
                    messagebox.showerror("Erro", "A quantidade deve ser um número inteiro positivo.")
                    return
                
                # Validação do preço
                preco = preco_var.get()
                try:
                    preco = float(preco)
                    if preco < 0:
                        raise ValueError("O preço não pode ser negativo.")
                except ValueError:
                    messagebox.showerror("Erro", "O preço deve ser um número válido.")
                    return
                
                # Adiciona a peça ao serviço
                self.add_part(
                    part_data[0],  # ID
                    part_data[1],  # Descrição
                    part_data[3] if part_data[3] != 'NULL' else None,  # Código de barras
                    preco,         # Preço unitário
                    quantidade     # Quantidade
                )
                
                # Atualiza o CSV se necessário
                if atualizar_csv_var.get():
                    try:
                        preco_formatado = preco
                        self.csv_manager.update_part_price(part_data[0], preco_formatado)
                        messagebox.showinfo("Sucesso", "Preço atualizado no CSV com sucesso.")
                    except Exception as e:
                        logger.error(f"Erro ao atualizar preço no CSV: {e}")
                        messagebox.showerror("Erro", f"Erro ao atualizar preço no CSV: {str(e)}")
                
                dialog.destroy()
                
            except Exception as e:
                logger.error(f"Erro ao adicionar peça: {e}")
                messagebox.showerror("Erro", f"Erro ao adicionar peça: {str(e)}")
        
        ttk.Button(
            buttons_frame, 
            text="Confirmar", 
            command=confirm_add
        ).pack(side=tk.RIGHT, padx=5)
        
        # Foco inicial no campo de quantidade
        quantidade_entry.focus_set()
    
    def add_part(self, peca_id, descricao, codigo_barras, preco_unitario, quantidade):
        """
        Adiciona uma peça ao serviço.
        
        Args:
            peca_id (int): ID da peça
            descricao (str): Descrição da peça
            codigo_barras (str): Código de barras da peça
            preco_unitario (float): Preço unitário
            quantidade (int): Quantidade
        """
        # Verifica se a peça já foi adicionada
        for i, peca in enumerate(self.servico.pecas):
            if peca['peca_id'] == peca_id:
                # Atualiza a quantidade
                self.servico.pecas[i]['quantidade'] += quantidade
                self.servico.pecas[i]['valor_total'] = (
                    self.servico.pecas[i]['quantidade'] * 
                    self.servico.pecas[i]['preco_unitario']
                )
                
                # Atualiza a interface
                self.update_parts_list()
                self.update_summary()
                return
        
        # Adiciona a peça ao serviço
        self.servico.add_peca(
            peca_id,
            descricao,
            codigo_barras,
            preco_unitario,
            quantidade
        )
        
        # Atualiza a interface
        self.update_parts_list()
        self.update_summary()
    
    def remove_part(self):
        """Remove a peça selecionada da lista."""
        selection = self.added_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione uma peça para remover.")
            return
        
        # Índice da peça selecionada
        index = self.added_tree.index(selection[0])
        
        # Remove a peça
        if self.servico.remove_peca(index):
            # Atualiza a interface
            self.update_parts_list()
            self.update_summary()
        else:
            messagebox.showerror("Erro", "Erro ao remover a peça.")
    
    def edit_part_quantity(self):
        """Edita a quantidade de uma peça já adicionada."""
        selection = self.added_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione uma peça para editar.")
            return
        
        # Índice da peça selecionada
        index = self.added_tree.index(selection[0])
        
        # Obtém a peça
        if index < len(self.servico.pecas):
            peca = self.servico.pecas[index]
            
            # Cria uma janela de diálogo
            dialog = tk.Toplevel(self)
            dialog.title("Editar Quantidade")
            dialog.geometry("300x150")
            dialog.transient(self)
            dialog.resizable(False, False)
            dialog.grab_set()
            
            # Container principal
            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Campo de quantidade
            ttk.Label(main_frame, text="Nova Quantidade:").grid(row=0, column=0, padx=5, pady=10)
            
            quantidade_var = tk.StringVar(value=str(peca['quantidade']))
            quantidade_entry = ttk.Entry(main_frame, width=10, textvariable=quantidade_var)
            quantidade_entry.grid(row=0, column=1, padx=5, pady=10)
            
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
                    # Validação da quantidade
                    nova_quantidade = quantidade_var.get()
                    try:
                        nova_quantidade = int(nova_quantidade)
                        if nova_quantidade <= 0:
                            raise ValueError("A quantidade deve ser maior que zero.")
                    except ValueError:
                        messagebox.showerror("Erro", "A quantidade deve ser um número inteiro positivo.")
                        return
                    
                    # Atualiza a quantidade
                    self.servico.pecas[index]['quantidade'] = nova_quantidade
                    self.servico.pecas[index]['valor_total'] = (
                        nova_quantidade * self.servico.pecas[index]['preco_unitario']
                    )
                    
                    # Atualiza a interface
                    self.update_parts_list()
                    self.update_summary()
                    
                    dialog.destroy()
                    
                except Exception as e:
                    logger.error(f"Erro ao editar quantidade: {e}")
                    messagebox.showerror("Erro", f"Erro ao editar quantidade: {str(e)}")
            
            ttk.Button(
                buttons_frame, 
                text="Confirmar", 
                command=confirm_edit
            ).pack(side=tk.RIGHT, padx=5)
            
            # Foco inicial no campo de quantidade
            quantidade_entry.focus_set()
            quantidade_entry.selection_range(0, tk.END)
    
    def update_parts_list(self):
        """Atualiza a lista de peças na interface."""
        # Limpa a lista atual
        for item in self.added_tree.get_children():
            self.added_tree.delete(item)
        
        # Adiciona as peças à lista
        for peca in self.servico.pecas:
            self.added_tree.insert(
                "", 
                tk.END, 
                values=(
                    peca['descricao'],
                    peca['quantidade'],
                    format_currency(peca['preco_unitario']),
                    format_currency(peca['valor_total'])
                )
            )
    
    def update_summary(self):
        """Atualiza o resumo do serviço."""
        # Valor do serviço
        try:
            valor_servico = float(self.valor_servico_var.get() or 0)
        except ValueError:
            valor_servico = 0.0
        
        self.servico.valor_servico = valor_servico
        
        # Atualiza os labels
        self.summary_service_value.config(text=format_currency(valor_servico))
        self.summary_parts_value.config(text=format_currency(self.servico.get_valor_total_pecas()))
        self.summary_total_value.config(text=format_currency(self.servico.get_valor_total()))
    
    def new_service(self):
        """Inicializa um novo serviço."""
        self.servico = Servico()
        
        # Reseta campos
        self.cliente_var.set("")
        self.telefone_var.set("")
        self.descricao_text.delete("1.0", tk.END)
        self.char_count_var.set("0/500 caracteres")
        
        # Recarrega mecânicos
        self.load_mecanicos()
        
        self.valor_servico_var.set("0.00")
        self.porcentagem_var.set("0")
        
        # Limpa listas
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for item in self.added_tree.get_children():
            self.added_tree.delete(item)
        
        # Atualiza título
        self.title_label.config(text="Novo Serviço")
        
        # Atualiza resumo
        self.update_summary()
    
    def load_service(self, servico_id):
        """
        Carrega um serviço existente para edição.
        
        Args:
            servico_id (int): ID do serviço a ser carregado
        """
        try:
            # Carrega o serviço do banco de dados
            servico_data = Servico.get_by_id(servico_id)
            
            if not servico_data:
                messagebox.showerror("Erro", f"Serviço #{servico_id} não encontrado.")
                return
            
            # Cria objeto do serviço
            self.servico = Servico(**dict(servico_data))
            
            # Carrega as peças
            pecas = self.servico.get_pecas()
            self.servico.pecas = []
            
            for peca in pecas:
                self.servico.add_peca(
                    peca['peca_id'],
                    peca['descricao'],
                    peca['codigo_barras'],
                    peca['preco_unitario'],
                    peca['quantidade']
                )
            
            # Atualiza a interface
            self.cliente_var.set(self.servico.cliente)
            self.telefone_var.set(self.servico.telefone)
            
            self.descricao_text.delete("1.0", tk.END)
            self.descricao_text.insert("1.0", self.servico.descricao)
            self.char_count_var.set(f"{len(self.servico.descricao)}/500 caracteres")
            
            self.valor_servico_var.set(f"{self.servico.valor_servico:.2f}")
            self.porcentagem_var.set(str(int(self.servico.porcentagem_mecanico)))
            
            # Seleciona o mecânico
            self.load_mecanicos()
            for i, value in enumerate(self.mecanico_combobox['values']):
                if f"ID: {self.servico.mecanico_id})" in value:
                    self.mecanico_combobox.current(i)
                    break
            
            # Atualiza listas
            self.update_parts_list()
            
            # Atualiza título
            self.title_label.config(text=f"Editar Serviço #{self.servico.id}")
            
            # Atualiza resumo
            self.update_summary()
            
        except Exception as e:
            logger.error(f"Erro ao carregar serviço: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar serviço: {str(e)}")
    
    def validate_form(self):
        """
        Valida o formulário antes de salvar.
        
        Returns:
            bool: True se o formulário é válido, False caso contrário
        """
        errors = []
        
        # Cliente
        if not self.cliente_var.get().strip():
            errors.append("O nome do cliente é obrigatório.")
        
        # Telefone
        telefone = self.telefone_var.get().strip()
        if not telefone:
            errors.append("O telefone é obrigatório.")
        else:
            valid, msg = validate_phone(telefone)
            if not valid:
                errors.append(msg)
        
        # Descrição
        descricao = self.descricao_text.get("1.0", tk.END).strip()
        if not descricao:
            errors.append("A descrição da mão de obra é obrigatória.")
        
        # Mecânico
        if not self.mecanico_var.get():
            errors.append("É necessário selecionar um mecânico.")
        
        # Valor do serviço
        try:
            valor_servico = float(self.valor_servico_var.get() or 0)
            if valor_servico < 0:
                errors.append("O valor do serviço não pode ser negativo.")
        except ValueError:
            errors.append("O valor do serviço deve ser um número válido.")
        
        # Porcentagem
        try:
            porcentagem = int(self.porcentagem_var.get() or 0)
            if porcentagem < 0 or porcentagem > 100:
                errors.append("A porcentagem do mecânico deve estar entre 0 e 100.")
        except ValueError:
            errors.append("A porcentagem do mecânico deve ser um número inteiro.")
        
        # Exibe erros, se houver
        if errors:
            messagebox.showerror(
                "Erros no Formulário",
                "Corrija os seguintes erros antes de salvar:\n\n" + "\n".join([f"- {e}" for e in errors])
            )
            return False
        
        return True
    
    def save_service(self):
        """Salva o serviço no banco de dados."""
        if not self.validate_form():
            return
        
        try:
            # Atualiza os dados do serviço
            self.servico.cliente = self.cliente_var.get().strip()
            self.servico.telefone = self.telefone_var.get().strip()
            self.servico.descricao = self.descricao_text.get("1.0", tk.END).strip()
            
            # Extrai o ID do mecânico
            mecanico_str = self.mecanico_var.get()
            mecanico_id = int(re.search(r"ID: (\d+)\)", mecanico_str).group(1))
            self.servico.mecanico_id = mecanico_id
            
            self.servico.valor_servico = float(self.valor_servico_var.get() or 0)
            self.servico.porcentagem_mecanico = int(self.porcentagem_var.get() or 0)
            
            # Salva o serviço
            self.servico.save()
            
            messagebox.showinfo(
                "Sucesso",
                f"Serviço #{self.servico.id} salvo com sucesso!"
            )
            
            # Navega para a aba de relatórios
            self.main_window.navigate_to("relatorios")
            
        except Exception as e:
            logger.error(f"Erro ao salvar serviço: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar serviço: {str(e)}")
    
    def cancel_service(self):
        """Cancela a edição/criação do serviço."""
        if messagebox.askyesno(
            "Cancelar",
            "Deseja realmente cancelar? Todas as alterações serão perdidas."
        ):
            self.main_window.navigate_to("painel")
    
    def generate_pdf(self):
        """Gera o PDF do serviço conforme o tipo selecionado."""
        if not self.servico.id:
            if not self.validate_form():
                return
            
            if messagebox.askyesno(
                "Serviço não Salvo",
                "O serviço ainda não foi salvo. Deseja salvá-lo antes de gerar o PDF?"
            ):
                self.save_service()
                return
        
        try:
            tipo_relatorio = self.report_type.get()
            
            if tipo_relatorio == "cliente":
                pdf_path = generate_pdf_cliente(self.servico)
            elif tipo_relatorio == "mecanico":
                pdf_path = generate_pdf_mecanico(self.servico)
            elif tipo_relatorio == "loja":
                pdf_path = generate_pdf_loja(self.servico)
            else:
                messagebox.showerror("Erro", "Tipo de relatório inválido.")
                return
            
            messagebox.showinfo(
                "PDF Gerado",
                f"Relatório gerado com sucesso em:\n{pdf_path}"
            )
            
            # Abre o PDF no visualizador padrão
            import os
            import subprocess
            import platform
            
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', pdf_path))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(pdf_path)
            else:  # Linux
                subprocess.call(('xdg-open', pdf_path))
                
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {str(e)}")
    
    def on_navigate(self, action=None, servico_id=None):
        """
        Método chamado quando o usuário navega para esta aba.
        
        Args:
            action (str): Ação a ser executada ('new' para novo serviço)
            servico_id (int): ID do serviço a ser carregado (para edição)
        """
        if action == "new":
            self.new_service()
        elif servico_id:
            self.load_service(servico_id)
    
    def on_tab_selected(self):
        """Método chamado quando a aba é selecionada."""
        self.main_window.set_status("Cadastro de Serviço")
