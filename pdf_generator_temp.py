"""
Gerador de PDF para serviços
Responsável por gerar PDF para cliente, mecânico e loja.
"""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, mm
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


class PDFGenerator:
    """
    Classe para geração de PDF de serviços.
    Gera diferentes tipos de relatórios:
    - Cliente: comprovante em tamanho 80mm x 200mm (largura específica para comprovantes)
    - Mecânico: relatório com serviços e valores a receber
    - Loja: relatório com serviços, peças e valores totais
    - Extrato: relatório com movimentações financeiras de uma carteira
    """
    
    def __init__(self):
        """Inicializa o gerador de PDF."""
        # Criar diretórios para armazenar PDFs se não existirem
        self.cliente_dir = os.path.join(os.getcwd(), 'ser cliente')
        self.mecanico_dir = os.path.join(os.getcwd(), 'ser mecanico')
        self.loja_dir = os.path.join(os.getcwd(), 'ser loja')
        self.extratos_dir = os.path.join(os.getcwd(), 'extratos')
        
        os.makedirs(self.cliente_dir, exist_ok=True)
        os.makedirs(self.mecanico_dir, exist_ok=True)
        os.makedirs(self.loja_dir, exist_ok=True)
        os.makedirs(self.extratos_dir, exist_ok=True)
    
    def gerar_pdf_cliente(self, servico, config=None):
        """
        Gera PDF para o cliente (tamanho 80mm x 200mm).
        
        Args:
            servico (dict): Dados do serviço
            config (dict, optional): Configurações da empresa
            
        Returns:
            str: Caminho para o arquivo PDF gerado
        """
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        if servico['id'] == 0:  # Preview antes de salvar
            filepath = os.path.join(self.cliente_dir, f"preview_cliente.pdf")
        else:
            codigo_servico = f"{servico['mecanico_nome'][0].upper()}{servico['id']}" if servico['mecanico_nome'] else f"S{servico['id']}"
            filepath = os.path.join(self.cliente_dir, f"servico_{codigo_servico}_cliente.pdf")
        
        # Definir tamanho do papel: 80mm x 200mm
        pagesize = (80 * mm, 200 * mm)
        
        # Criar documento
        doc = SimpleDocTemplate(
            filepath,
            pagesize=pagesize,
            rightMargin=5*mm,
            leftMargin=5*mm,
            topMargin=5*mm,
            bottomMargin=5*mm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Center',
            alignment=TA_CENTER,
            fontSize=9,
        ))
        styles.add(ParagraphStyle(
            name='CenterBold',
            parent=styles['Center'],
            fontName='Helvetica-Bold'
        ))
        styles.add(ParagraphStyle(
            name='Right',
            alignment=TA_RIGHT,
            fontSize=8,
        ))
        styles.add(ParagraphStyle(
            name='SmallNormal',
            parent=styles['Normal'],
            fontSize=7,
        ))
        
        # Conteúdo do documento
        elements = []
        
        # Cabeçalho com informações da empresa
        if config:
            elements.append(Paragraph(f"<b>{config.get('nome_empresa', 'Monark Motopeças')}</b>", styles["CenterBold"]))
            if config.get('endereco'):
                elements.append(Paragraph(f"{config.get('endereco')}", styles["Center"]))
            if config.get('telefone'):
                elements.append(Paragraph(f"Tel: {config.get('telefone')}", styles["Center"]))
        else:
            elements.append(Paragraph("<b>Monark Motopeças e Bicicletaria</b>", styles["CenterBold"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Informações do serviço
        codigo_servico = f"{servico['mecanico_nome'][0].upper()}{servico['id']}" if servico['mecanico_nome'] else f"S{servico['id']}"
        if servico['id'] == 0:  # Preview
            codigo_servico = "PREVIEW"
            
        elements.append(Paragraph(f"<b>SERVIÇO: {codigo_servico}</b>", styles["CenterBold"]))
        elements.append(Paragraph(f"Data: {data_atual}", styles["Center"]))
        elements.append(Spacer(1, 3*mm))
        
        # Dados do cliente em maiúsculo
        data = [
            ["CLIENTE:", servico['cliente'].upper()],
            ["TELEFONE:", servico['telefone'].upper()],
            ["MECÂNICO:", servico['mecanico_nome'].upper()],
        ]
        
        t = Table(data, colWidths=[20*mm, 50*mm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 3*mm))
        
        # Descrição do serviço em maiúsculo
        elements.append(Paragraph("<b>DESCRIÇÃO:</b>", styles["SmallNormal"]))
        elements.append(Paragraph(servico['descricao'].upper(), styles["SmallNormal"]))
        
        elements.append(Spacer(1, 3*mm))
        
        # Tabela de peças
        if servico['pecas'] and len(servico['pecas']) > 0:
            elements.append(Paragraph("<b>PEÇAS UTILIZADAS:</b>", styles["SmallNormal"]))
            
            # Cabeçalho da tabela
            data = [
                ["Qtd", "Descrição", "Unitário", "Total"]
            ]
            
            # Adicionar linhas de peças
            for peca in servico['pecas']:
                valor_unitario = float(peca.get('preco_unitario', 0))
                quantidade = int(peca.get('quantidade', 0))
                total = valor_unitario * quantidade
                
                data.append([
                    str(quantidade),
                    peca.get('descricao', 'N/A').upper(),
                    f"R$ {valor_unitario:.2f}".replace('.', ','),
                    f"R$ {total:.2f}".replace('.', ',')
                ])
            
            # Adicionar linha de total
            data.append([
                "",
                "",
                "<b>TOTAL PEÇAS:</b>",
                f"<b>R$ {servico['valor_total_pecas']:.2f}</b>".replace('.', ',')
            ])
            
            # Criar tabela
            t = Table(data, colWidths=[7*mm, 31*mm, 15*mm, 17*mm])
            t.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, 0), 0.5, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEBELOW', (0, -2), (-1, -2), 0.5, colors.black),
            ]))
            elements.append(t)
            
            elements.append(Spacer(1, 3*mm))
        
        # Valor do serviço e total
        valor_servico = float(servico.get('valor_servico', 0))
        valor_total_pecas = float(servico.get('valor_total_pecas', 0))
        valor_total = valor_servico + valor_total_pecas
        
        data = [
            ["MÃO DE OBRA:", f"R$ {valor_servico:.2f}".replace('.', ',')],
            ["PEÇAS:", f"R$ {valor_total_pecas:.2f}".replace('.', ',')],
            ["TOTAL:", f"R$ {valor_total:.2f}".replace('.', ',')],
        ]
        
        t = Table(data, colWidths=[40*mm, 30*mm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEBELOW', (0, -2), (-1, -2), 0.5, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 5*mm))
        
        # Assinaturas
        elements.append(Paragraph("<b>AUTORIZAÇÃO DE SERVIÇO</b>", styles["Center"]))
        elements.append(Spacer(1, 10*mm))
        
        data = [
            ["_______________________", "_______________________"],
            ["Cliente", "Mecânico"],
        ]
        
        t = Table(data, colWidths=[35*mm, 35*mm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        
        # Rodapé
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph("Obrigado pela preferência!", styles["Center"]))
        
        # Construir o documento
        doc.build(elements)
        
        return filepath
    
    def gerar_pdf_mecanico(self, servico, config=None):
        """
        Gera PDF para o mecânico (tamanho 80mm x extrato).
        
        Args:
            servico (dict): Dados do serviço
            config (dict, optional): Configurações da empresa
            
        Returns:
            str: Caminho para o arquivo PDF gerado
        """
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        if servico['id'] == 0:  # Preview antes de salvar
            filepath = os.path.join(self.mecanico_dir, f"preview_mecanico.pdf")
        else:
            codigo_servico = f"{servico['mecanico_nome'][0].upper()}{servico['id']}" if servico['mecanico_nome'] else f"S{servico['id']}"
            filepath = os.path.join(self.mecanico_dir, f"servico_{codigo_servico}_mecanico.pdf")
        
        # Criar documento tamanho 80mm x extrato
        doc = SimpleDocTemplate(
            filepath,
            pagesize=(80*mm, 297*mm),  # Largura 80mm, altura da página A4
            rightMargin=5*mm,
            leftMargin=5*mm,
            topMargin=10*mm,
            bottomMargin=10*mm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Center',
            alignment=TA_CENTER,
            fontSize=9,
        ))
        styles.add(ParagraphStyle(
            name='TitleMecanico',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=12,
        ))
        styles.add(ParagraphStyle(
            name='Right',
            alignment=TA_RIGHT,
            fontSize=8,
        ))
        styles.add(ParagraphStyle(
            name='SmallNormal',
            parent=styles['Normal'],
            fontSize=8,
        ))
        
        # Conteúdo do documento
        elements = []
        
        # Cabeçalho com informações da empresa
        if config:
            elements.append(Paragraph(f"<b>{config.get('nome_empresa', 'Monark Motopeças')}</b>", styles["TitleMecanico"]))
            if config.get('endereco'):
                elements.append(Paragraph(f"{config.get('endereco')}", styles["Center"]))
            if config.get('telefone'):
                elements.append(Paragraph(f"Tel: {config.get('telefone')}", styles["Center"]))
        else:
            elements.append(Paragraph("<b>Monark Motopeças e Bicicletaria</b>", styles["TitleMecanico"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Título do documento
        codigo_servico = f"{servico['mecanico_nome'][0].upper()}{servico['id']}" if servico['mecanico_nome'] else f"S{servico['id']}"
        if servico['id'] == 0:  # Preview
            codigo_servico = "PREVIEW"
            
        elements.append(Paragraph(f"<b>RELATÓRIO PARA MECÂNICO - {codigo_servico}</b>", styles["TitleMecanico"]))
        elements.append(Paragraph(f"Data: {data_atual}", styles["Center"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Dados do serviço
        data = [
            ["Mecânico:", servico['mecanico_nome'].upper()],
            ["Cliente:", servico['cliente'].upper()],
            ["Telefone:", servico['telefone'].upper()],
            ["Data:", data_atual],
        ]
        
        t = Table(data, colWidths=[25*mm, 45*mm])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 5*mm))
        
        # Descrição do serviço
        elements.append(Paragraph("<b>Descrição do Serviço:</b>", styles["SmallNormal"]))
        elements.append(Paragraph(servico['descricao'].upper(), styles["SmallNormal"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Cálculo de valores
        valor_servico = float(servico.get('valor_servico', 0))
        porcentagem = servico.get('porcentagem_mecanico', 80)
        valor_mecanico = (valor_servico * porcentagem) / 100
        
        # Resumo de valores
        data = [
            ["Valor do Serviço:", f"R$ {valor_servico:.2f}".replace('.', ',')],
            ["Porcentagem do Mecânico:", f"{porcentagem}%"],
            ["Valor a Receber:", f"R$ {valor_mecanico:.2f}".replace('.', ',')],
        ]
        
        t = Table(data, colWidths=[45*mm, 25*mm])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, -2), (-1, -2), 0.5, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 10*mm))
        
        # Assinaturas
        data = [
            ["_______________________", "_______________________"],
            ["Mecânico", "Responsável"],
        ]
        
        t = Table(data, colWidths=[35*mm, 35*mm])
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        
        # Construir o documento
        doc.build(elements)
        
        return filepath
    
    def gerar_pdf_loja(self, servico, config=None):
        """
        Gera PDF para a loja (tamanho 80mm x extrato).
        
        Args:
            servico (dict): Dados do serviço
            config (dict, optional): Configurações da empresa
            
        Returns:
            str: Caminho para o arquivo PDF gerado
        """
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        if servico['id'] == 0:  # Preview antes de salvar
            filepath = os.path.join(self.loja_dir, f"preview_loja.pdf")
        else:
            codigo_servico = f"{servico['mecanico_nome'][0].upper()}{servico['id']}" if servico['mecanico_nome'] else f"S{servico['id']}"
            filepath = os.path.join(self.loja_dir, f"servico_{codigo_servico}_loja.pdf")
        
        # Criar documento tamanho 80mm x extrato
        doc = SimpleDocTemplate(
            filepath,
            pagesize=(80*mm, 297*mm),  # Largura 80mm, altura da página A4
            rightMargin=5*mm,
            leftMargin=5*mm,
            topMargin=10*mm,
            bottomMargin=10*mm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Center',
            alignment=TA_CENTER,
            fontSize=9,
        ))
        styles.add(ParagraphStyle(
            name='TitleLoja',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=12,
        ))
        styles.add(ParagraphStyle(
            name='Right',
            alignment=TA_RIGHT,
            fontSize=8,
        ))
        styles.add(ParagraphStyle(
            name='SmallNormal',
            parent=styles['Normal'],
            fontSize=8,
        ))
        
        # Conteúdo do documento
        elements = []
        
        # Cabeçalho com informações da empresa
        if config:
            elements.append(Paragraph(f"<b>{config.get('nome_empresa', 'Monark Motopeças')}</b>", styles["TitleLoja"]))
            if config.get('endereco'):
                elements.append(Paragraph(f"{config.get('endereco')}", styles["Center"]))
            if config.get('telefone'):
                elements.append(Paragraph(f"Tel: {config.get('telefone')}", styles["Center"]))
        else:
            elements.append(Paragraph("<b>Monark Motopeças e Bicicletaria</b>", styles["TitleLoja"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Título do documento
        codigo_servico = f"{servico['mecanico_nome'][0].upper()}{servico['id']}" if servico['mecanico_nome'] else f"S{servico['id']}"
        if servico['id'] == 0:  # Preview
            codigo_servico = "PREVIEW"
            
        elements.append(Paragraph(f"<b>RELATÓRIO FINANCEIRO - {codigo_servico}</b>", styles["TitleLoja"]))
        elements.append(Paragraph(f"Data: {data_atual}", styles["Center"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Dados do serviço
        data = [
            ["Mecânico:", servico['mecanico_nome'].upper()],
            ["Cliente:", servico['cliente'].upper()],
            ["Telefone:", servico['telefone']],
            ["Data:", data_atual],
        ]
        
        t = Table(data, colWidths=[25*mm, 45*mm])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 5*mm))
        
        # Descrição do serviço
        elements.append(Paragraph("<b>Descrição do Serviço:</b>", styles["SmallNormal"]))
        elements.append(Paragraph(servico['descricao'].upper(), styles["SmallNormal"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Tabela de peças
        if servico['pecas'] and len(servico['pecas']) > 0:
            elements.append(Paragraph("<b>Peças Utilizadas:</b>", styles["SmallNormal"]))
            
            # Cabeçalho da tabela
            data = [
                ["ID", "Descrição", "Preço", "Qtd", "Total"]
            ]
            
            # Adicionar linhas de peças
            for peca in servico['pecas']:
                valor_unitario = float(peca.get('preco_unitario', 0))
                quantidade = int(peca.get('quantidade', 0))
                total = valor_unitario * quantidade
                
                data.append([
                    peca.get('peca_id', 'N/A'),
                    peca.get('descricao', 'N/A'),
                    f"R$ {valor_unitario:.2f}".replace('.', ','),
                    str(quantidade),
                    f"R$ {total:.2f}".replace('.', ',')
                ])
            
            # Adicionar linha de total
            data.append([
                "",
                "",
                "",
                "<b>TOTAL:</b>",
                f"<b>R$ {servico['valor_total_pecas']:.2f}</b>".replace('.', ',')
            ])
            
            # Criar tabela
            colWidths = [12*mm, 21*mm, 15*mm, 10*mm, 17*mm]
            t = Table(data, colWidths=colWidths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 0), (4, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (3, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
                ('SPAN', (0, -1), (2, -1)),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
            ]))
            elements.append(t)
            
            elements.append(Spacer(1, 5*mm))
        
        # Cálculo de valores
        valor_servico = float(servico.get('valor_servico', 0))
        valor_total_pecas = float(servico.get('valor_total_pecas', 0))
        porcentagem = servico.get('porcentagem_mecanico', 80)
        valor_mecanico = (valor_servico * porcentagem) / 100
        valor_loja_servico = valor_servico - valor_mecanico
        valor_total_loja = valor_loja_servico + valor_total_pecas
        valor_total_geral = valor_servico + valor_total_pecas
        
        # Resumo financeiro
        elements.append(Paragraph("<b>Resumo Financeiro:</b>", styles["SmallNormal"]))
        
        data = [
            ["DESCRIÇÃO", "VALOR", "TOTAL"],
            ["Serviço (100%)", f"R$ {valor_servico:.2f}".replace('.', ','), ""],
            ["Mecânico ({0}%)".format(porcentagem), f"R$ {valor_mecanico:.2f}".replace('.', ','), ""],
            ["Loja ({0}%)".format(100-porcentagem), f"R$ {valor_loja_servico:.2f}".replace('.', ','), ""],
            ["Peças (100% Loja)", f"R$ {valor_total_pecas:.2f}".replace('.', ','), ""],
            ["Total Loja", "", f"R$ {valor_total_loja:.2f}".replace('.', ',')],
            ["TOTAL GERAL", "", f"R$ {valor_total_geral:.2f}".replace('.', ',')],
        ]
        
        t = Table(data, colWidths=[35*mm, 22*mm, 18*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, 0), 0.5, colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -2), (-1, -2), 0.5, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        
        # Construir o documento
        doc.build(elements)
        
        return filepath