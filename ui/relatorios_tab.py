# -*- coding: utf-8 -*-

"""
Aba Relatórios
Permite visualizar relatórios de serviços e exportar PDFs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import datetime
import subprocess
import platform

from models import Servico, Mecanico
from services.pdf_generator import generate_pdf_cliente, generate_pdf_mecanico, generate_pdf_loja
from utils.formatters import format_currency, format_date, format_phone

logger = logging.getLogger(__name__)

class RelatoriosTab(ttk.Frame):
    """
    Classe que representa a aba Relatórios, onde é possível visualizar e exportar relatórios.
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
        logger.debug("Aba Relatórios inicializada")
    
    def setup_ui(self):
        """Configura a interface da aba Relatórios."""
        # Container principal
        self.main_container = ttk.Frame(self, padding=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            self.main_container,
            text="Relatórios de Serviços",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Frame de filtros
        filter_frame = ttk.LabelFrame(self.main_container, text="Filtros")
        filter_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Layout de filtros
        filter_inner = ttk.Frame(filter_frame, padding=10)
        filter_inner.pack(fill=tk.X)
        
        # Filtro por período
        ttk.Label(filter_inner, text="Período:").grid(row=0, column=0, padx=5, pady=5)
        
        periodo_frame = ttk.Frame(filter_inner)
        periodo_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(periodo_frame, text="De:").pack(side=tk.LEFT, padx=2)
        self.data_inicio_var = tk.StringVar()
        ttk.Entry(periodo_frame, width=10, textvariable=self.data_inicio_var).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(periodo_frame, text="Até:").pack(side=tk.LEFT, padx=2)
        self.data_fim_var = tk.StringVar()
        ttk.Entry(periodo_frame, width=10, textvariable=self.data_fim_var).pack(side=tk.LEFT, padx=2)
        
        # Filtro por mecânico
        ttk.Label(filter_inner, text="Mecânico:").grid(row=0, column=2, padx=5, pady=5)
        
        self.mecanico_var = tk.StringVar()
        self.mecanico_combobox = ttk.Combobox(filter_inner, width=30, textvariable=self.mecanico_var, state="readonly")
        self.mecanico_combobox.grid(row=0, column=3, padx=5, pady=5)
        
        # Filtro por status
        ttk.Label(filter_inner, text="Status:").grid(row=1, column=0, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="todos")
        status_frame = ttk.Frame(filter_inner)
        status_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Radiobutton(status_frame, text="Todos", variable=self.status_var, value="todos").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(status_frame, text="Em Andamento", variable=self.status_var, value="em_andamento").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(status_frame, text="Concluídos", variable=self.status_var, value="concluido").pack(side=tk.LEFT, padx=5)
        
        # Botões de filtro
        filter_buttons = ttk.Frame(filter_inner)
        filter_buttons.grid(row=1, column=2, columnspan=2, sticky=tk.E, padx=5, pady=5)
        
        ttk.Button(
            filter_buttons,
            text="Aplicar Filtros",
            command=self.apply_filters
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            filter_buttons,
            text="Limpar Filtros",
            command=self.clear_filters
        ).pack(side=tk.LEFT, padx=5)
        
        # Frame para lista de serviços
        list_frame = ttk.LabelFrame(self.main_container, text="Serviços")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview para lista de serviços
        self.servicos_tree = ttk.Treeview(
            list_frame, 
            columns=("id", "cliente", "telefone", "mecanico", "data", "valor", "status"),
            show="headings",
            height=15
        )
        
        # Configuração das colunas
        self.servicos_tree.heading("id", text="ID")
        self.servicos_tree.heading("cliente", text="Cliente")
        self.servicos_tree.heading("telefone", text="Telefone")
        self.servicos_tree.heading("mecanico", text="Mecânico")
        self.servicos_tree.heading("data", text="Data")
        self.servicos_tree.heading("valor", text="Valor Total")
        self.servicos_tree.heading("status", text="Status")
        
        self.servicos_tree.column("id", width=50, anchor=tk.CENTER)
        self.servicos_tree.column("cliente", width=200)
        self.servicos_tree.column("telefone", width=100, anchor=tk.CENTER)
        self.servicos_tree.column("mecanico", width=150)
        self.servicos_tree.column("data", width=150, anchor=tk.CENTER)
        self.servicos_tree.column("valor", width=100, anchor=tk.CENTER)
        self.servicos_tree.column("status", width=100, anchor=tk.CENTER)
        
        # Scrollbar para lista de serviços
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.servicos_tree.yview)
        self.servicos_tree.configure(yscrollcommand=scrollbar.set)
        
        self.servicos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click para visualizar detalhes do serviço
        self.servicos_tree.bind("<Double-1>", lambda e: self.view_service_details())
        
        # Frame para botões de ação
        buttons_frame = ttk.Frame(self.main_container)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Botão para visualizar detalhes
        ttk.Button(
            buttons_frame,
            text="Visualizar Detalhes",
            command=self.view_service_details
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão para editar serviço
        ttk.Button(
            buttons_frame,
            text="Editar Serviço",
            command=self.edit_service
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão para concluir serviço
        self.btn_concluir = ttk.Button(
            buttons_frame,
            text="Concluir Serviço",
            command=self.complete_service
        )
        self.btn_concluir.pack(side=tk.LEFT, padx=5)
        
        # Botão para gerar relatório
        report_frame = ttk.Frame(buttons_frame)
        report_frame.pack(side=tk.RIGHT)
        
        self.report_type_var = tk.StringVar(value="cliente")
        report_types = ttk.Combobox(
            report_frame,
            values=["cliente", "mecanico", "loja"],
            textvariable=self.report_type_var,
            state="readonly",
            width=10
        )
        report_types.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            report_frame,
            text="Gerar PDF",
            command=self.generate_pdf
        ).pack(side=tk.LEFT, padx=5)
        
        # Carrega mecânicos para o combobox
        self.load_mecanicos()
        
        # Carrega a lista de serviços
        self.load_servicos()
    
    def load_mecanicos(self):
        """Carrega os mecânicos do banco de dados para o combobox."""
        # Lista de mecânicos para o filtro
        mecanicos = Mecanico.get_all()
        
        # Adiciona opção para todos os mecânicos
        mecanicos_list = ["Todos os Mecânicos"]
        
        # Adiciona os mecânicos
        for mecanico in mecanicos:
            mecanicos_list.append(f"{mecanico['nome']} (ID: {mecanico['id']})")
        
        # Atualiza o combobox
        self.mecanico_combobox['values'] = mecanicos_list
        self.mecanico_combobox.current(0)  # Seleciona "Todos os Mecânicos"
    
    def load_servicos(self, mecanico_id=None, data_inicio=None, data_fim=None, status=None):
        """
        Carrega os serviços do banco de dados para a treeview.
        
        Args:
            mecanico_id (int): ID do mecânico para filtrar
            data_inicio (str): Data inicial para filtro (formato: YYYY-MM-DD)
            data_fim (str): Data final para filtro (formato: YYYY-MM-DD)
            status (str): Status para filtro ('em_andamento', 'concluido' ou None para todos)
        """
        # Limpa a lista atual
        for item in self.servicos_tree.get_children():
            self.servicos_tree.delete(item)
        
        try:
            # Constrói a query
            query = "SELECT s.*, m.nome as mecanico_nome FROM servicos s "
            query += "LEFT JOIN mecanicos m ON s.mecanico_id = m.id WHERE 1=1 "
            params = []
            
            # Adiciona filtros
            if mecanico_id:
                query += "AND s.mecanico_id = ? "
                params.append(mecanico_id)
            
            if data_inicio:
                query += "AND s.data_cadastro >= ? "
                params.append(f"{data_inicio} 00:00:00")
            
            if data_fim:
                query += "AND s.data_cadastro <= ? "
                params.append(f"{data_fim} 23:59:59")
            
            if status and status != "todos":
                query += "AND s.status = ? "
                params.append(status)
            
            query += "ORDER BY s.data_cadastro DESC"
            
            # Executa a query
            from database import execute_query
            servicos = execute_query(query, tuple(params), fetch_all=True)
            
            # Adiciona à treeview
            for servico in servicos:
                # Carrega as peças para calcular o valor total
                servico_obj = Servico(**dict(servico))
                pecas = servico_obj.get_pecas()
                
                # Adiciona as peças ao objeto
                for peca in pecas:
                    servico_obj.add_peca(
                        peca['peca_id'],
                        peca['descricao'],
                        peca['codigo_barras'],
                        peca['preco_unitario'],
                        peca['quantidade']
                    )
                
                # Valor total
                valor_total = servico_obj.get_valor_total()
                
                # Status formatado
                status_formatado = "Em Andamento" if servico['status'] == 'em_andamento' else "Concluído"
                
                # Formata a data
                data_formatada = format_date(servico['data_cadastro'])
                
                # Formata o telefone
                telefone_formatado = format_phone(servico['telefone'])
                
                # Adiciona à treeview
                self.servicos_tree.insert(
                    "", 
                    tk.END, 
                    values=(
                        servico['id'],
                        servico['cliente'],
                        telefone_formatado,
                        servico['mecanico_nome'] or "N/A",
                        data_formatada,
                        format_currency(valor_total),
                        status_formatado
                    ),
                    tags=(servico['status'],)
                )
            
            # Configura as cores de acordo com o status
            self.servicos_tree.tag_configure("em_andamento", background="#FFFFD1")
            self.servicos_tree.tag_configure("concluido", background="#D1FFD1")
            
            # Atualiza o status da barra de status
            if servicos:
                self.main_window.set_status(f"Relatórios - {len(servicos)} serviço(s) encontrado(s)")
            else:
                self.main_window.set_status("Relatórios - Nenhum serviço encontrado")
            
        except Exception as e:
            logger.error(f"Erro ao carregar serviços: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar serviços: {str(e)}")
    
    def apply_filters(self):
        """Aplica os filtros selecionados à lista de serviços."""
        # Obtém os filtros
        data_inicio = self.data_inicio_var.get().strip()
        data_fim = self.data_fim_var.get().strip()
        mecanico_str = self.mecanico_var.get()
        status = self.status_var.get()
        
        # Validação de datas
        if data_inicio and not self._validate_date_format(data_inicio):
            messagebox.showerror("Erro", "Formato de data inicial inválido. Use YYYY-MM-DD.")
            return
        
        if data_fim and not self._validate_date_format(data_fim):
            messagebox.showerror("Erro", "Formato de data final inválido. Use YYYY-MM-DD.")
            return
        
        # Extrai o ID do mecânico, se não for "Todos os Mecânicos"
        mecanico_id = None
        if mecanico_str and mecanico_str != "Todos os Mecânicos":
            try:
                mecanico_id = int(mecanico_str.split("ID: ")[1].strip(")"))
            except (IndexError, ValueError):
                pass
        
        # Carrega os serviços com os filtros
        self.load_servicos(mecanico_id, data_inicio, data_fim, status)
    
    def clear_filters(self):
        """Limpa os filtros e recarrega todos os serviços."""
        self.data_inicio_var.set("")
        self.data_fim_var.set("")
        self.mecanico_combobox.current(0)  # Seleciona "Todos os Mecânicos"
        self.status_var.set("todos")
        
        # Recarrega os serviços sem filtros
        self.load_servicos()
    
    def view_service_details(self):
        """Exibe os detalhes de um serviço selecionado."""
        selection = self.servicos_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione um serviço para visualizar os detalhes.")
            return
        
        # Obtém os dados do serviço selecionado
        item = self.servicos_tree.item(selection[0])
        servico_data = item['values']
        
        # Carrega o serviço do banco de dados
        servico = Servico.get_by_id(servico_data[0])
        
        if not servico:
            messagebox.showerror("Erro", "Serviço não encontrado no banco de dados.")
            return
        
        # Carrega as peças
        servico_obj = Servico(**dict(servico))
        pecas = servico_obj.get_pecas()
        
        # Cria uma janela de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Detalhes do Serviço #{servico['id']}")
        dialog.geometry("650x500")
        dialog.transient(self)
        dialog.resizable(True, True)
        dialog.grab_set()
        
        # Container principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(
            main_frame,
            text=f"Serviço #{servico['id']}",
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 10))
        
        # Notebook para abas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Aba de informações gerais
        info_frame = ttk.Frame(notebook, padding=10)
        notebook.add(info_frame, text="Informações Gerais")
        
        # Informações do serviço
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # Cliente
        ttk.Label(info_grid, text="Cliente:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_grid, text=servico['cliente']).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Telefone
        ttk.Label(info_grid, text="Telefone:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_grid, text=format_phone(servico['telefone'])).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Mecânico
        ttk.Label(info_grid, text="Mecânico:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        mecanico = Mecanico.get_by_id(servico['mecanico_id'])
        ttk.Label(info_grid, text=mecanico['nome'] if mecanico else "N/A").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Data de Cadastro
        ttk.Label(info_grid, text="Data de Cadastro:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_grid, text=format_date(servico['data_cadastro'])).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Data de Conclusão
        ttk.Label(info_grid, text="Data de Conclusão:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_grid, text=format_date(servico['data_conclusao']) if servico['data_conclusao'] else "Em aberto").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Status
        ttk.Label(info_grid, text="Status:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        status_text = "Em Andamento" if servico['status'] == 'em_andamento' else "Concluído"
        ttk.Label(info_grid, text=status_text).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Valor do Serviço
        ttk.Label(info_grid, text="Valor da Mão de Obra:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_grid, text=format_currency(servico['valor_servico'])).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Porcentagem do Mecânico
        ttk.Label(info_grid, text="Porcentagem do Mecânico:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_grid, text=f"{servico['porcentagem_mecanico']}%").grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
        row += 1
        
        # Aba de descrição
        desc_frame = ttk.Frame(notebook, padding=10)
        notebook.add(desc_frame, text="Descrição do Serviço")
        
        # Descrição em formato texto
        desc_text = tk.Text(desc_frame, wrap=tk.WORD, height=10, width=60)
        desc_text.pack(fill=tk.BOTH, expand=True)
        
        desc_text.insert(tk.END, servico['descricao'] or "")
        desc_text.config(state=tk.DISABLED)  # Somente leitura
        
        # Aba de peças
        pecas_frame = ttk.Frame(notebook, padding=10)
        notebook.add(pecas_frame, text="Peças Utilizadas")
        
        # Treeview para peças
        pecas_tree = ttk.Treeview(
            pecas_frame, 
            columns=("descricao", "quantidade", "preco", "total"),
            show="headings",
            height=8
        )
        
        # Configuração das colunas
        pecas_tree.heading("descricao", text="Descrição")
        pecas_tree.heading("quantidade", text="Qtd")
        pecas_tree.heading("preco", text="Preço Unit.")
        pecas_tree.heading("total", text="Total")
        
        pecas_tree.column("descricao", width=300)
        pecas_tree.column("quantidade", width=50, anchor=tk.CENTER)
        pecas_tree.column("preco", width=100, anchor=tk.CENTER)
        pecas_tree.column("total", width=100, anchor=tk.CENTER)
        
        # Scrollbar para peças
        pecas_scrollbar = ttk.Scrollbar(pecas_frame, orient=tk.VERTICAL, command=pecas_tree.yview)
        pecas_tree.configure(yscrollcommand=pecas_scrollbar.set)
        
        pecas_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pecas_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Preenche a treeview com as peças
        valor_total_pecas = 0
        for peca in pecas:
            pecas_tree.insert(
                "", 
                tk.END, 
                values=(
                    peca['descricao'],
                    peca['quantidade'],
                    format_currency(peca['preco_unitario']),
                    format_currency(peca['valor_total'])
                )
            )
            valor_total_pecas += peca['valor_total']
        
        # Frame para resumo de valores
        values_frame = ttk.Frame(main_frame)
        values_frame.pack(fill=tk.X, pady=10)
        
        # Resumo de valores
        ttk.Label(values_frame, text="Valor da Mão de Obra:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(values_frame, text=format_currency(servico['valor_servico'])).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(values_frame, text="Valor das Peças:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(values_frame, text=format_currency(valor_total_pecas)).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(values_frame, text="VALOR TOTAL:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(values_frame, text=format_currency(servico['valor_servico'] + valor_total_pecas), font=('Arial', 10, 'bold')).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Botões de ação
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Botão de fechar
        ttk.Button(
            buttons_frame, 
            text="Fechar", 
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Botão de gerar PDF
        ttk.Button(
            buttons_frame, 
            text="Gerar PDF", 
            command=lambda: self.generate_service_pdf(servico_obj)
        ).pack(side=tk.LEFT, padx=5)
    
    def edit_service(self):
        """Navega para a aba de serviço para editar o serviço selecionado."""
        selection = self.servicos_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione um serviço para editar.")
            return
        
        # Obtém os dados do serviço selecionado
        item = self.servicos_tree.item(selection[0])
        servico_data = item['values']
        
        # Navega para a aba de serviço com o ID do serviço
        self.main_window.navigate_to("servico", servico_id=servico_data[0])
    
    def complete_service(self):
        """Marca um serviço como concluído."""
        selection = self.servicos_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione um serviço para concluir.")
            return
        
        # Obtém os dados do serviço selecionado
        item = self.servicos_tree.item(selection[0])
        servico_data = item['values']
        
        # Carrega o serviço do banco de dados
        servico = Servico.get_by_id(servico_data[0])
        
        if not servico:
            messagebox.showerror("Erro", "Serviço não encontrado no banco de dados.")
            return
        
        # Verifica se o serviço já está concluído
        if servico['status'] == 'concluido':
            messagebox.showinfo("Informação", "Este serviço já está concluído.")
            return
        
        # Confirmação
        if not messagebox.askyesno(
            "Confirmar Conclusão",
            f"Deseja realmente marcar o serviço #{servico['id']} como concluído?\n\n"
            "Isso atualizará as carteiras do mecânico e da loja com os valores correspondentes."
        ):
            return
        
        try:
            # Atualiza o serviço
            servico_obj = Servico(**dict(servico))
            servico_obj.status = 'concluido'
            servico_obj.data_conclusao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Carrega as peças
            pecas = servico_obj.get_pecas()
            for peca in pecas:
                servico_obj.add_peca(
                    peca['peca_id'],
                    peca['descricao'],
                    peca['codigo_barras'],
                    peca['preco_unitario'],
                    peca['quantidade']
                )
            
            # Salva o serviço (isso atualizará as carteiras automaticamente)
            servico_obj.save()
            
            messagebox.showinfo("Sucesso", f"Serviço #{servico['id']} concluído com sucesso!")
            
            # Recarrega a lista de serviços
            self.apply_filters()
            
        except Exception as e:
            logger.error(f"Erro ao concluir serviço: {e}")
            messagebox.showerror("Erro", f"Erro ao concluir serviço: {str(e)}")
    
    def generate_pdf(self):
        """Gera o PDF do serviço selecionado conforme o tipo escolhido."""
        selection = self.servicos_tree.selection()
        
        if not selection:
            messagebox.showinfo("Seleção", "Selecione um serviço para gerar o PDF.")
            return
        
        # Obtém os dados do serviço selecionado
        item = self.servicos_tree.item(selection[0])
        servico_data = item['values']
        
        # Carrega o serviço do banco de dados
        servico = Servico.get_by_id(servico_data[0])
        
        if not servico:
            messagebox.showerror("Erro", "Serviço não encontrado no banco de dados.")
            return
        
        # Cria objeto do serviço
        servico_obj = Servico(**dict(servico))
        
        # Carrega as peças
        pecas = servico_obj.get_pecas()
        for peca in pecas:
            servico_obj.add_peca(
                peca['peca_id'],
                peca['descricao'],
                peca['codigo_barras'],
                peca['preco_unitario'],
                peca['quantidade']
            )
        
        # Gera o PDF de acordo com o tipo selecionado
        self.generate_service_pdf(servico_obj)
    
    def generate_service_pdf(self, servico):
        """
        Gera o PDF de um serviço.
        
        Args:
            servico (Servico): Objeto do serviço
        """
        tipo_relatorio = self.report_type_var.get()
        
        try:
            if tipo_relatorio == "cliente":
                pdf_path = generate_pdf_cliente(servico)
            elif tipo_relatorio == "mecanico":
                pdf_path = generate_pdf_mecanico(servico)
            elif tipo_relatorio == "loja":
                pdf_path = generate_pdf_loja(servico)
            else:
                messagebox.showerror("Erro", "Tipo de relatório inválido.")
                return
            
            messagebox.showinfo(
                "PDF Gerado",
                f"Relatório gerado com sucesso em:\n{pdf_path}"
            )
            
            # Abre o PDF no visualizador padrão
            self.open_pdf(pdf_path)
                
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar PDF: {str(e)}")
    
    def open_pdf(self, pdf_path):
        """
        Abre um arquivo PDF no visualizador padrão do sistema.
        
        Args:
            pdf_path (str): Caminho do arquivo PDF
        """
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', pdf_path))
            elif platform.system() == 'Windows':  # Windows
                os.startfile(pdf_path)
            else:  # Linux
                subprocess.call(('xdg-open', pdf_path))
        except Exception as e:
            logger.error(f"Erro ao abrir PDF: {e}")
            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir o PDF. O arquivo foi salvo em {pdf_path}."
            )
    
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
    
    def on_tab_selected(self):
        """Método chamado quando a aba é selecionada."""
        self.main_window.set_status("Relatórios de Serviços")
        
        # Recarrega as listas ao selecionar a aba
        self.load_mecanicos()
        self.load_servicos()
