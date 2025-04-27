# -*- coding: utf-8 -*-

"""
Gerador de PDFs
Responsável por gerar PDFs de relatórios de serviços para clientes, mecânicos e loja.
"""

import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                              TableStyle, Image)

from models import Mecanico, Servico, Configuracao
from utils.formatters import format_currency, format_date, format_phone

logger = logging.getLogger(__name__)

def get_config_paths():
    """
    Obtém os caminhos para os diretórios de relatórios a partir das configurações.
    
    Returns:
        tuple: (cliente_path, mecanico_path, loja_path)
    """
    cliente_path = "ser cliente"
    mecanico_path = "ser mecanico"
    loja_path = "ser loja"
    
    try:
        # Carrega as configurações do banco de dados
        config = Configuracao.get()
        
        if config:
            # Verifica se existem caminhos personalizados
            for path_name in ['dir_cliente', 'dir_mecanico', 'dir_loja']:
                if path_name in config and config[path_name]:
                    if path_name == 'dir_cliente':
                        cliente_path = config[path_name]
                    elif path_name == 'dir_mecanico':
                        mecanico_path = config[path_name]
                    elif path_name == 'dir_loja':
                        loja_path = config[path_name]
    except Exception as e:
        logger.error(f"Erro ao obter caminhos das configurações: {e}")
    
    # Cria os diretórios se não existirem
    for path in [cliente_path, mecanico_path, loja_path]:
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                logger.info(f"Diretório criado: {path}")
            except Exception as e:
                logger.error(f"Erro ao criar diretório {path}: {e}")
    
    return cliente_path, mecanico_path, loja_path

def get_company_info():
    """
    Obtém informações da empresa das configurações.
    
    Returns:
        dict: Dicionário com informações da empresa
    """
    info = {
        'nome': 'Monark Motopeças e Bicicletaria',
        'endereco': '',
        'telefone': ''
    }
    
    try:
        # Carrega as configurações do banco de dados
        config = Configuracao.get()
        
        if config:
            if 'nome_empresa' in config and config['nome_empresa']:
                info['nome'] = config['nome_empresa']
            if 'endereco' in config and config['endereco']:
                info['endereco'] = config['endereco']
            if 'telefone' in config and config['telefone']:
                info['telefone'] = config['telefone']
    except Exception as e:
        logger.error(f"Erro ao obter informações da empresa: {e}")
    
    return info

def generate_pdf_cliente(servico):
    """
    Gera um PDF de recibo para o cliente.
    
    Args:
        servico (Servico): Objeto do serviço
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Obtem o caminho do diretório para salvar o PDF
    cliente_path, _, _ = get_config_paths()
    
    # Nome do arquivo PDF
    pdf_filename = f"OS_{servico.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(cliente_path, pdf_filename)
    
    # Informações da empresa
    company_info = get_company_info()
    
    # Tamanho de recibo (80mm x 200mm)
    receipt_width = 80 * mm
    receipt_height = 200 * mm
    
    # Cria o documento PDF
    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=(receipt_width, receipt_height),
        rightMargin=5*mm, 
        leftMargin=5*mm,
        topMargin=5*mm, 
        bottomMargin=5*mm
    )
    
    # Estilos de texto
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=10,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Normal_Centered',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Normal_Small',
        parent=styles['Normal'],
        fontSize=8
    ))
    styles.add(ParagraphStyle(
        name='Normal_Bold',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='Table_Header',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        alignment=1  # Centralizado
    ))
    
    # Elementos do documento
    elements = []
    
    # Título da empresa
    elements.append(Paragraph(company_info['nome'], styles['Title']))
    
    if company_info['endereco']:
        elements.append(Paragraph(company_info['endereco'], styles['Normal_Centered']))
    
    if company_info['telefone']:
        elements.append(Paragraph(f"Tel: {format_phone(company_info['telefone'])}", styles['Normal_Centered']))
    
    elements.append(Spacer(1, 5*mm))
    
    # Título do recibo
    elements.append(Paragraph(f"AUTORIZAÇÃO DE SERVIÇO #{servico.id}", styles['Title']))
    elements.append(Spacer(1, 3*mm))
    
    # Data e hora
    data_hora = format_date(servico.data_cadastro)
    elements.append(Paragraph(f"Data: {data_hora}", styles['Normal_Small']))
    
    # Informações do cliente
    elements.append(Paragraph(f"Cliente: {servico.cliente}", styles['Normal_Small']))
    elements.append(Paragraph(f"Telefone: {format_phone(servico.telefone)}", styles['Normal_Small']))
    
    # Informações do mecânico
    mecanico = Mecanico.get_by_id(servico.mecanico_id)
    if mecanico:
        elements.append(Paragraph(f"Mecânico: {mecanico['nome']}", styles['Normal_Small']))
    
    elements.append(Spacer(1, 3*mm))
    
    # Descrição do serviço
    elements.append(Paragraph("DESCRIÇÃO DO SERVIÇO:", styles['Normal_Bold']))
    elements.append(Paragraph(servico.descricao, styles['Normal_Small']))
    
    elements.append(Spacer(1, 3*mm))
    
    # Lista de peças
    if servico.pecas:
        elements.append(Paragraph("PEÇAS UTILIZADAS:", styles['Normal_Bold']))
        
        # Cabeçalho da tabela
        table_data = [
            [
                Paragraph("Descrição", styles['Table_Header']),
                Paragraph("Qtd", styles['Table_Header']),
                Paragraph("Valor", styles['Table_Header'])
            ]
        ]
        
        # Dados da tabela
        for peca in servico.pecas:
            table_data.append([
                Paragraph(peca['descricao'][:30], styles['Normal_Small']),
                Paragraph(str(peca['quantidade']), styles['Normal_Small']),
                Paragraph(format_currency(peca['valor_total']), styles['Normal_Small'])
            ])
        
        # Estilo da tabela
        table_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ])
        
        # Criação da tabela
        table = Table(table_data, colWidths=[40*mm, 10*mm, 20*mm])
        table.setStyle(table_style)
        elements.append(table)
        
        elements.append(Spacer(1, 3*mm))
    
    # Resumo de valores
    valor_pecas = servico.get_valor_total_pecas()
    valor_total = servico.get_valor_total()
    
    # Tabela para valores
    value_data = [
        [Paragraph("Mão de Obra:", styles['Normal_Bold']), Paragraph(format_currency(servico.valor_servico), styles['Normal_Small'])],
        [Paragraph("Peças:", styles['Normal_Bold']), Paragraph(format_currency(valor_pecas), styles['Normal_Small'])],
        [Paragraph("TOTAL:", styles['Normal_Bold']), Paragraph(format_currency(valor_total), styles['Normal_Bold'])]
    ]
    
    value_table = Table(value_data, colWidths=[40*mm, 30*mm])
    value_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('LINEBELOW', (0, -2), (-1, -2), 0.5, colors.black),
    ]))
    elements.append(value_table)
    
    elements.append(Spacer(1, 5*mm))
    
    # Termos e condições
    terms = [
        "TERMOS E CONDIÇÕES:",
        "1. A garantia dos serviços e peças é de 90 dias.",
        "2. Peças substituídas serão entregues ao cliente se solicitado.",
        "3. O prazo de entrega será informado pelo mecânico responsável."
    ]
    
    for term in terms:
        elements.append(Paragraph(term, styles['Normal_Small']))
    
    elements.append(Spacer(1, 10*mm))
    
    # Assinaturas
    sign_data = [
        ["_________________________", "_________________________"],
        ["Assinatura do Cliente", "Assinatura do Mecânico"]
    ]
    
    sign_table = Table(sign_data, colWidths=[35*mm, 35*mm])
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(sign_table)
    
    # Gera o PDF
    try:
        doc.build(elements)
        logger.info(f"PDF do cliente gerado com sucesso: {pdf_path}")
        return pdf_path
    
    except Exception as e:
        logger.error(f"Erro ao gerar PDF do cliente: {e}")
        raise

def generate_pdf_mecanico(servico):
    """
    Gera um PDF de relatório para o mecânico.
    
    Args:
        servico (Servico): Objeto do serviço
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Obtem o caminho do diretório para salvar o PDF
    _, mecanico_path, _ = get_config_paths()
    
    # Nome do arquivo PDF
    pdf_filename = f"Mecanico_OS_{servico.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(mecanico_path, pdf_filename)
    
    # Informações da empresa
    company_info = get_company_info()
    
    # Cria o documento PDF (tamanho A4)
    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=A4,
        rightMargin=15*mm, 
        leftMargin=15*mm,
        topMargin=15*mm, 
        bottomMargin=15*mm
    )
    
    # Estilos de texto
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Normal_Centered',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Normal_Bold',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='Table_Header',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        alignment=1  # Centralizado
    ))
    
    # Elementos do documento
    elements = []
    
    # Título da empresa
    elements.append(Paragraph(company_info['nome'], styles['Title']))
    
    if company_info['endereco']:
        elements.append(Paragraph(company_info['endereco'], styles['Normal_Centered']))
    
    if company_info['telefone']:
        elements.append(Paragraph(f"Tel: {format_phone(company_info['telefone'])}", styles['Normal_Centered']))
    
    elements.append(Spacer(1, 5*mm))
    
    # Obter informações do mecânico
    mecanico = Mecanico.get_by_id(servico.mecanico_id)
    mecanico_nome = mecanico['nome'] if mecanico else "Mecânico Não Identificado"
    
    # Título do relatório
    elements.append(Paragraph(f"RELATÓRIO DE SERVIÇO - MECÂNICO", styles['Subtitle']))
    elements.append(Paragraph(f"Mecânico: {mecanico_nome}", styles['Normal_Bold']))
    elements.append(Spacer(1, 5*mm))
    
    # Informações do serviço
    elements.append(Paragraph(f"Ordem de Serviço: #{servico.id}", styles['Normal']))
    elements.append(Paragraph(f"Data: {format_date(servico.data_cadastro)}", styles['Normal']))
    elements.append(Paragraph(f"Cliente: {servico.cliente}", styles['Normal']))
    elements.append(Paragraph(f"Telefone: {format_phone(servico.telefone)}", styles['Normal']))
    
    elements.append(Spacer(1, 5*mm))
    
    # Descrição do serviço
    elements.append(Paragraph("DESCRIÇÃO DO SERVIÇO:", styles['Normal_Bold']))
    elements.append(Paragraph(servico.descricao, styles['Normal']))
    
    elements.append(Spacer(1, 5*mm))
    
    # Tabela com peças utilizadas
    if servico.pecas:
        elements.append(Paragraph("PEÇAS UTILIZADAS:", styles['Normal_Bold']))
        
        # Cabeçalho da tabela
        table_data = [
            [
                Paragraph("Descrição", styles['Table_Header']),
                Paragraph("Código", styles['Table_Header']),
                Paragraph("Qtd", styles['Table_Header']),
                Paragraph("Valor Unit.", styles['Table_Header']),
                Paragraph("Valor Total", styles['Table_Header'])
            ]
        ]
        
        # Dados da tabela
        for peca in servico.pecas:
            table_data.append([
                Paragraph(peca['descricao'], styles['Normal']),
                Paragraph(str(peca['peca_id']), styles['Normal']),
                Paragraph(str(peca['quantidade']), styles['Normal']),
                Paragraph(format_currency(peca['preco_unitario']), styles['Normal']),
                Paragraph(format_currency(peca['valor_total']), styles['Normal'])
            ])
        
        # Estilo da tabela
        table_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ])
        
        # Criação da tabela
        table = Table(table_data, colWidths=[200, 60, 40, 80, 80])
        table.setStyle(table_style)
        elements.append(table)
        
        elements.append(Spacer(1, 5*mm))
    
    # Valores e comissão do mecânico
    valor_pecas = servico.get_valor_total_pecas()
    valor_servico = servico.valor_servico
    valor_mecanico = valor_servico * (servico.porcentagem_mecanico / 100)
    
    elements.append(Paragraph("VALORES E COMISSÃO:", styles['Normal_Bold']))
    
    # Tabela para valores
    value_data = [
        ["Valor da Mão de Obra:", format_currency(valor_servico)],
        ["Porcentagem do Mecânico:", f"{servico.porcentagem_mecanico}%"],
        ["Valor da Comissão:", format_currency(valor_mecanico)],
        ["Valor das Peças (Total):", format_currency(valor_pecas)]
    ]
    
    value_table = Table(value_data, colWidths=[250, 100])
    value_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elements.append(value_table)
    
    # Informações adicionais
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("INFORMAÇÕES ADICIONAIS:", styles['Normal_Bold']))
    if servico.status == 'concluido' and servico.data_conclusao:
        elements.append(Paragraph(f"Serviço concluído em: {format_date(servico.data_conclusao)}", styles['Normal']))
    else:
        elements.append(Paragraph("Serviço em andamento", styles['Normal']))
    
    # Observações
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("OBSERVAÇÕES:", styles['Normal_Bold']))
    elements.append(Paragraph("Este documento serve como comprovante do serviço realizado e da comissão devida ao mecânico.", styles['Normal']))
    
    # Data de geração do relatório
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal_Centered']))
    
    # Gera o PDF
    try:
        doc.build(elements)
        logger.info(f"PDF do mecânico gerado com sucesso: {pdf_path}")
        return pdf_path
    
    except Exception as e:
        logger.error(f"Erro ao gerar PDF do mecânico: {e}")
        raise

def generate_pdf_loja(servico):
    """
    Gera um PDF de relatório para a loja.
    
    Args:
        servico (Servico): Objeto do serviço
        
    Returns:
        str: Caminho do arquivo PDF gerado
    """
    # Obtem o caminho do diretório para salvar o PDF
    _, _, loja_path = get_config_paths()
    
    # Nome do arquivo PDF
    pdf_filename = f"Loja_OS_{servico.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(loja_path, pdf_filename)
    
    # Informações da empresa
    company_info = get_company_info()
    
    # Cria o documento PDF (tamanho A4)
    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=A4,
        rightMargin=15*mm, 
        leftMargin=15*mm,
        topMargin=15*mm, 
        bottomMargin=15*mm
    )
    
    # Estilos de texto
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Normal_Centered',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1  # Centralizado
    ))
    styles.add(ParagraphStyle(
        name='Normal_Bold',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='Table_Header',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        alignment=1  # Centralizado
    ))
    
    # Elementos do documento
    elements = []
    
    # Título da empresa
    elements.append(Paragraph(company_info['nome'], styles['Title']))
    
    if company_info['endereco']:
        elements.append(Paragraph(company_info['endereco'], styles['Normal_Centered']))
    
    if company_info['telefone']:
        elements.append(Paragraph(f"Tel: {format_phone(company_info['telefone'])}", styles['Normal_Centered']))
    
    elements.append(Spacer(1, 5*mm))
    
    # Título do relatório
    elements.append(Paragraph(f"RELATÓRIO FINANCEIRO DE SERVIÇO", styles['Subtitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Informações do serviço
    elements.append(Paragraph(f"Ordem de Serviço: #{servico.id}", styles['Normal']))
    elements.append(Paragraph(f"Data: {format_date(servico.data_cadastro)}", styles['Normal']))
    elements.append(Paragraph(f"Cliente: {servico.cliente}", styles['Normal']))
    elements.append(Paragraph(f"Telefone: {format_phone(servico.telefone)}", styles['Normal']))
    
    # Obter informações do mecânico
    mecanico = Mecanico.get_by_id(servico.mecanico_id)
    mecanico_nome = mecanico['nome'] if mecanico else "Mecânico Não Identificado"
    elements.append(Paragraph(f"Mecânico: {mecanico_nome}", styles['Normal']))
    
    elements.append(Spacer(1, 5*mm))
    
    # Resumo financeiro
    elements.append(Paragraph("RESUMO FINANCEIRO:", styles['Normal_Bold']))
    
    # Valores
    valor_servico = servico.valor_servico
    valor_mecanico = valor_servico * (servico.porcentagem_mecanico / 100)
    valor_loja_servico = valor_servico - valor_mecanico
    valor_pecas = servico.get_valor_total_pecas()
    valor_total_loja = valor_loja_servico + valor_pecas
    
    # Tabela para valores financeiros
    value_data = [
        ["Valor da Mão de Obra:", format_currency(valor_servico)],
        ["Comissão do Mecânico ({}%):".format(servico.porcentagem_mecanico), format_currency(valor_mecanico)],
        ["Valor para a Loja (Mão de Obra):", format_currency(valor_loja_servico)],
        ["Valor das Peças:", format_currency(valor_pecas)],
        ["VALOR TOTAL PARA A LOJA:", format_currency(valor_total_loja)]
    ]
    
    value_table = Table(value_data, colWidths=[250, 100])
    value_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(value_table)
    
    elements.append(Spacer(1, 5*mm))
    
    # Tabela com peças vendidas
    if servico.pecas:
        elements.append(Paragraph("DETALHAMENTO DE PEÇAS VENDIDAS:", styles['Normal_Bold']))
        
        # Cabeçalho da tabela
        table_data = [
            [
                Paragraph("Código", styles['Table_Header']),
                Paragraph("Descrição", styles['Table_Header']),
                Paragraph("Qtd", styles['Table_Header']),
                Paragraph("Valor Unit.", styles['Table_Header']),
                Paragraph("Valor Total", styles['Table_Header'])
            ]
        ]
        
        # Dados da tabela
        for peca in servico.pecas:
            table_data.append([
                Paragraph(str(peca['peca_id']), styles['Normal']),
                Paragraph(peca['descricao'], styles['Normal']),
                Paragraph(str(peca['quantidade']), styles['Normal']),
                Paragraph(format_currency(peca['preco_unitario']), styles['Normal']),
                Paragraph(format_currency(peca['valor_total']), styles['Normal'])
            ])
        
        # Estilo da tabela
        table_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ])
        
        # Criação da tabela
        table = Table(table_data, colWidths=[60, 200, 40, 80, 80])
        table.setStyle(table_style)
        elements.append(table)
    
    # Status do serviço
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("STATUS DO SERVIÇO:", styles['Normal_Bold']))
    if servico.status == 'concluido' and servico.data_conclusao:
        elements.append(Paragraph(f"Serviço concluído em: {format_date(servico.data_conclusao)}", styles['Normal']))
        elements.append(Paragraph("Os valores já foram adicionados às carteiras correspondentes.", styles['Normal']))
    else:
        elements.append(Paragraph("Serviço em andamento", styles['Normal']))
        elements.append(Paragraph("Os valores serão adicionados às carteiras quando o serviço for concluído.", styles['Normal']))
    
    # Data de geração do relatório
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal_Centered']))
    
    # Gera o PDF
    try:
        doc.build(elements)
        logger.info(f"PDF da loja gerado com sucesso: {pdf_path}")
        return pdf_path
    
    except Exception as e:
        logger.error(f"Erro ao gerar PDF da loja: {e}")
        raise
