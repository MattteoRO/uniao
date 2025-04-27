"""
Gerador de PDF
Responsável por gerar os relatórios em PDF para cliente, mecânico e loja.
"""
import os
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFGenerator:
    """
    Classe responsável por gerar os diferentes relatórios em PDF.
    """
    def __init__(self):
        """Inicializa o gerador de PDF."""
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            name='TitleStyle',
            parent=self.styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=16,
            spaceAfter=10*mm
        )
        self.normal_style = self.styles['Normal']
        self.heading_style = self.styles['Heading2']
        self.subtitle_style = ParagraphStyle(
            name='SubtitleStyle',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=6*mm
        )
        self.table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Verificar se as pastas de destino existem
        for folder in ['ser cliente', 'ser mecanico', 'ser loja']:
            if not os.path.exists(folder):
                os.makedirs(folder)
    
    def _gerar_codigo_servico(self, nome_mecanico, id_servico):
        """
        Gera o código do serviço com base na primeira letra do nome do mecânico e ID.
        
        Args:
            nome_mecanico (str): Nome do mecânico
            id_servico (int): ID do serviço
            
        Returns:
            str: Código do serviço no formato "X123" (primeira letra + ID)
        """
        if not nome_mecanico:
            return f"S{id_servico}"
            
        primeira_letra = nome_mecanico[0].upper()
        return f"{primeira_letra}{id_servico}"
    
    def gerar_pdf_cliente(self, servico, configuracoes, abrir_automaticamente=True):
        """
        Gera o relatório PDF para o cliente.
        
        Args:
            servico (dict): Dados do serviço
            configuracoes (dict): Configurações do sistema
            abrir_automaticamente (bool): Se True, abre o PDF após gerar
            
        Returns:
            str: Caminho para o PDF gerado
        """
        # Dimensões do recibo: 80mm x 200mm
        width = 80 * mm
        height = 200 * mm
        
        # Preparar dados
        id_servico = servico.get('id', 0)
        cliente = servico.get('cliente', 'Cliente')
        telefone = servico.get('telefone', '')
        descricao = servico.get('descricao', '')
        mecanico = servico.get('mecanico_nome', 'Mecânico')
        valor_servico = servico.get('valor_servico', 0)
        valor_total_pecas = servico.get('valor_total_pecas', 0)
        valor_total = valor_servico + valor_total_pecas
        data = servico.get('data_criacao', datetime.datetime.now())
        pecas = servico.get('pecas', [])
        
        # Gerar código do serviço
        codigo_servico = self._gerar_codigo_servico(mecanico, id_servico)
        
        # Definir caminho do arquivo
        now = datetime.datetime.now()
        filename = f"cliente_{cliente.replace(' ', '_')}_{codigo_servico}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('ser cliente', filename)
        
        # Criar documento
        doc = SimpleDocTemplate(filepath, pagesize=(width, height), 
                               rightMargin=5*mm, leftMargin=5*mm,
                               topMargin=5*mm, bottomMargin=5*mm)
        
        # Conteúdo
        elements = []
        
        # Título
        empresa = configuracoes.get('nome_empresa', 'Monark Motopeças e Bicicletaria')
        title = Paragraph(f"<b>{empresa}</b>", self.title_style)
        elements.append(title)
        
        # Subtítulo
        subtitle = Paragraph(f"<b>AUTORIZAÇÃO DE SERVIÇO {codigo_servico}</b>", self.subtitle_style)
        elements.append(subtitle)
        
        # Dados do cliente e serviço
        data_text = f"<b>Cliente:</b> {cliente}<br/>"
        if telefone:
            data_text += f"<b>Telefone:</b> {telefone}<br/>"
        data_text += f"<b>Mecânico:</b> {mecanico}<br/>"
        data_text += f"<b>Data:</b> {data.strftime('%d/%m/%Y')}<br/>"
        data_text += f"<b>Descrição:</b> {descricao}<br/>"
        
        p_data = Paragraph(data_text, self.normal_style)
        elements.append(p_data)
        elements.append(Spacer(1, 10))
        
        # Tabela de valores
        data = [
            ["Descrição", "Valor (R$)"],
            ["Mão de obra", f"{valor_servico:.2f}".replace('.', ',')],
            ["Peças", f"{valor_total_pecas:.2f}".replace('.', ',')],
            ["Total", f"{valor_total:.2f}".replace('.', ',')],
        ]
        
        t = Table(data, colWidths=[width*0.6, width*0.3])
        t.setStyle(self.table_style)
        elements.append(t)
        elements.append(Spacer(1, 10))
        
        # Tabela de peças
        if pecas:
            elements.append(Paragraph("<b>Peças utilizadas:</b>", self.subtitle_style))
            
            pecas_data = [["Descrição", "Qtd", "Valor (R$)"]]
            for peca in pecas:
                descricao_peca = peca.get('descricao', 'Peça')
                quantidade = peca.get('quantidade', 1)
                preco = peca.get('preco_unitario', 0) * quantidade
                pecas_data.append([
                    descricao_peca,
                    str(quantidade),
                    f"{preco:.2f}".replace('.', ','),
                ])
                
            t2 = Table(pecas_data, colWidths=[width*0.5, width*0.15, width*0.25])
            t2.setStyle(self.table_style)
            elements.append(t2)
        
        # Assinaturas
        elements.append(Spacer(1, 15*mm))
        assinatura = "_" * 20
        elements.append(Paragraph(f"{assinatura}<br/>Cliente", self.normal_style))
        
        # Gerar PDF
        doc.build(elements)
        
        # Se solicitado, abrir o PDF automaticamente
        if abrir_automaticamente:
            self._abrir_pdf(filepath)
            
        return filepath
    
    def gerar_pdf_mecanico(self, servico, configuracoes, abrir_automaticamente=True):
        """
        Gera o relatório PDF para o mecânico.
        
        Args:
            servico (dict): Dados do serviço
            configuracoes (dict): Configurações do sistema
            abrir_automaticamente (bool): Se True, abre o PDF após gerar
            
        Returns:
            str: Caminho para o PDF gerado
        """
        # Dimensões A4
        width, height = A4
        
        # Preparar dados
        id_servico = servico.get('id', 0)
        cliente = servico.get('cliente', 'Cliente')
        descricao = servico.get('descricao', '')
        mecanico = servico.get('mecanico_nome', 'Mecânico')
        mecanico_id = servico.get('mecanico_id', 0)
        valor_servico = servico.get('valor_servico', 0)
        porcentagem_mecanico = servico.get('porcentagem_mecanico', 80)
        valor_mecanico = (valor_servico * porcentagem_mecanico) / 100
        data = servico.get('data_criacao', datetime.datetime.now())
        
        # Gerar código do serviço
        codigo_servico = self._gerar_codigo_servico(mecanico, id_servico)
        
        # Definir caminho do arquivo
        now = datetime.datetime.now()
        filename = f"mecanico_{mecanico.replace(' ', '_')}_{codigo_servico}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('ser mecanico', filename)
        
        # Criar documento
        doc = SimpleDocTemplate(filepath, pagesize=A4, 
                               rightMargin=15*mm, leftMargin=15*mm,
                               topMargin=15*mm, bottomMargin=15*mm)
        
        # Conteúdo
        elements = []
        
        # Título
        empresa = configuracoes.get('nome_empresa', 'Monark Motopeças e Bicicletaria')
        title = Paragraph(f"<b>{empresa}</b>", self.title_style)
        elements.append(title)
        
        # Subtítulo
        subtitle = Paragraph(f"<b>RELATÓRIO DE SERVIÇO - MECÂNICO</b>", self.subtitle_style)
        elements.append(subtitle)
        
        # Dados do mecânico
        data_text = f"<b>Mecânico:</b> {mecanico}<br/>"
        data_text += f"<b>Data:</b> {data.strftime('%d/%m/%Y')}<br/>"
        data_text += f"<b>Código do Serviço:</b> {codigo_servico}<br/>"
        
        p_data = Paragraph(data_text, self.normal_style)
        elements.append(p_data)
        elements.append(Spacer(1, 10))
        
        # Detalhes do serviço
        elements.append(Paragraph("<b>Detalhes do Serviço</b>", self.subtitle_style))
        
        detail_text = f"<b>Cliente:</b> {cliente}<br/>"
        detail_text += f"<b>Descrição:</b> {descricao}<br/>"
        detail_text += f"<b>Valor do Serviço:</b> R$ {valor_servico:.2f}".replace('.', ',') + "<br/>"
        detail_text += f"<b>Porcentagem do Mecânico:</b> {porcentagem_mecanico}%<br/>"
        detail_text += f"<b>Valor para o Mecânico:</b> R$ {valor_mecanico:.2f}".replace('.', ',') + "<br/>"
        
        p_detail = Paragraph(detail_text, self.normal_style)
        elements.append(p_detail)
        elements.append(Spacer(1, 20))
        
        # Assinaturas
        elements.append(Spacer(1, 15*mm))
        assinatura = "_" * 20
        elements.append(Paragraph(f"{assinatura}<br/>Mecânico", self.normal_style))
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(f"{assinatura}<br/>Responsável Loja", self.normal_style))
        
        # Gerar PDF
        doc.build(elements)
        
        # Se solicitado, abrir o PDF automaticamente
        if abrir_automaticamente:
            self._abrir_pdf(filepath)
            
        return filepath
    
    def gerar_pdf_loja(self, servico, configuracoes, abrir_automaticamente=True):
        """
        Gera o relatório PDF para a loja.
        
        Args:
            servico (dict): Dados do serviço
            configuracoes (dict): Configurações do sistema
            abrir_automaticamente (bool): Se True, abre o PDF após gerar
            
        Returns:
            str: Caminho para o PDF gerado
        """
        # Dimensões A4
        width, height = A4
        
        # Preparar dados
        id_servico = servico.get('id', 0)
        cliente = servico.get('cliente', 'Cliente')
        descricao = servico.get('descricao', '')
        mecanico = servico.get('mecanico_nome', 'Mecânico')
        mecanico_id = servico.get('mecanico_id', 0)
        valor_servico = servico.get('valor_servico', 0)
        porcentagem_mecanico = servico.get('porcentagem_mecanico', 80)
        valor_mecanico = (valor_servico * porcentagem_mecanico) / 100
        valor_loja_servico = valor_servico - valor_mecanico
        valor_total_pecas = servico.get('valor_total_pecas', 0)
        valor_total = valor_servico + valor_total_pecas
        data = servico.get('data_criacao', datetime.datetime.now())
        pecas = servico.get('pecas', [])
        
        # Gerar código do serviço
        codigo_servico = self._gerar_codigo_servico(mecanico, id_servico)
        
        # Definir caminho do arquivo
        now = datetime.datetime.now()
        filename = f"loja_{codigo_servico}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('ser loja', filename)
        
        # Criar documento
        doc = SimpleDocTemplate(filepath, pagesize=A4, 
                               rightMargin=15*mm, leftMargin=15*mm,
                               topMargin=15*mm, bottomMargin=15*mm)
        
        # Conteúdo
        elements = []
        
        # Título
        empresa = configuracoes.get('nome_empresa', 'Monark Motopeças e Bicicletaria')
        title = Paragraph(f"<b>{empresa}</b>", self.title_style)
        elements.append(title)
        
        # Subtítulo
        subtitle = Paragraph(f"<b>RELATÓRIO DE SERVIÇO - LOJA</b>", self.subtitle_style)
        elements.append(subtitle)
        
        # Dados do serviço
        data_text = f"<b>Código do Serviço:</b> {codigo_servico}<br/>"
        data_text += f"<b>Data:</b> {data.strftime('%d/%m/%Y')}<br/>"
        data_text += f"<b>Cliente:</b> {cliente}<br/>"
        data_text += f"<b>Mecânico:</b> {mecanico}<br/>"
        data_text += f"<b>Descrição:</b> {descricao}<br/>"
        
        p_data = Paragraph(data_text, self.normal_style)
        elements.append(p_data)
        elements.append(Spacer(1, 10))
        
        # Resumo financeiro
        elements.append(Paragraph("<b>Resumo Financeiro</b>", self.subtitle_style))
        
        # Tabela de resumo
        resumo_data = [
            ["Descrição", "Valor (R$)"],
            ["Valor do Serviço (Mão de obra)", f"{valor_servico:.2f}".replace('.', ',')],
            ["Valor das Peças", f"{valor_total_pecas:.2f}".replace('.', ',')],
            ["Valor Total do Serviço", f"{valor_total:.2f}".replace('.', ',')],
            ["Porcentagem do Mecânico", f"{porcentagem_mecanico}%"],
            ["Valor para o Mecânico", f"{valor_mecanico:.2f}".replace('.', ',')],
            ["Valor para a Loja (Mão de obra)", f"{valor_loja_servico:.2f}".replace('.', ',')],
            ["Valor para a Loja (Peças)", f"{valor_total_pecas:.2f}".replace('.', ',')],
            ["Valor Total para a Loja", f"{(valor_loja_servico + valor_total_pecas):.2f}".replace('.', ',')],
        ]
        
        t = Table(resumo_data, colWidths=[width*0.6, width*0.2])
        t.setStyle(self.table_style)
        elements.append(t)
        elements.append(Spacer(1, 10))
        
        # Tabela de peças
        if pecas:
            elements.append(Paragraph("<b>Peças utilizadas:</b>", self.subtitle_style))
            
            pecas_data = [["ID", "Descrição", "Qtd", "Preço Unit. (R$)", "Total (R$)"]]
            for peca in pecas:
                peca_id = peca.get('peca_id', '')
                descricao_peca = peca.get('descricao', 'Peça')
                quantidade = peca.get('quantidade', 1)
                preco_unitario = peca.get('preco_unitario', 0)
                preco_total = preco_unitario * quantidade
                pecas_data.append([
                    peca_id,
                    descricao_peca,
                    str(quantidade),
                    f"{preco_unitario:.2f}".replace('.', ','),
                    f"{preco_total:.2f}".replace('.', ','),
                ])
                
            t2 = Table(pecas_data, colWidths=[width*0.1, width*0.4, width*0.1, width*0.15, width*0.15])
            t2.setStyle(self.table_style)
            elements.append(t2)
        
        # Assinaturas
        elements.append(Spacer(1, 15*mm))
        assinatura = "_" * 20
        elements.append(Paragraph(f"{assinatura}<br/>Responsável Loja", self.normal_style))
        
        # Gerar PDF
        doc.build(elements)
        
        # Se solicitado, abrir o PDF automaticamente
        if abrir_automaticamente:
            self._abrir_pdf(filepath)
            
        return filepath
    
    def _abrir_pdf(self, filepath):
        """
        Abre o PDF gerado.
        
        Args:
            filepath (str): Caminho para o arquivo PDF
        """
        try:
            import os
            import platform
            if platform.system() == 'Darwin':  # macOS
                os.system(f'open "{filepath}"')
            elif platform.system() == 'Windows':  # Windows
                os.system(f'start "" "{filepath}"')
            else:  # Linux e outros
                os.system(f'xdg-open "{filepath}"')
        except Exception as e:
            print(f"Erro ao abrir o PDF: {e}")