"""
Gerador de PDF para extratos da carteira do mecânico.
Responsável por gerar PDF de extrato financeiro.
"""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, mm
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


class PDFExtratoGenerator:
    """
    Classe para geração de PDF de extrato financeiro de mecânicos.
    Gera relatório detalhado com todas as movimentações da carteira.
    """
    
    def __init__(self):
        """Inicializa o gerador de PDF."""
        # Criar diretório para armazenar PDFs se não existir
        self.extratos_dir = os.path.join(os.getcwd(), 'extratos')
        os.makedirs(self.extratos_dir, exist_ok=True)
    
    def gerar_pdf_extrato_mecanico(self, mecanico, carteira, movimentacoes, config=None):
        """
        Gera PDF do extrato da carteira de um mecânico (tamanho 80mm x extrato).
        
        Args:
            mecanico (dict): Dados do mecânico
            carteira (dict): Dados da carteira
            movimentacoes (list): Lista de movimentações
            config (dict, optional): Configurações da empresa
            
        Returns:
            str: Caminho para o arquivo PDF gerado
        """
        data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
        filepath = os.path.join(self.extratos_dir, f"extrato_mecanico_{mecanico['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        
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
            name='TitleExtrato',
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
            elements.append(Paragraph(f"<b>{config.get('nome_empresa', 'Monark Motopeças')}</b>", styles["TitleExtrato"]))
            if config.get('endereco'):
                elements.append(Paragraph(f"{config.get('endereco')}", styles["Center"]))
            if config.get('telefone'):
                elements.append(Paragraph(f"Tel: {config.get('telefone')}", styles["Center"]))
        else:
            elements.append(Paragraph("<b>Monark Motopeças e Bicicletaria</b>", styles["TitleExtrato"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Título do documento
        elements.append(Paragraph(f"<b>EXTRATO FINANCEIRO</b>", styles["TitleExtrato"]))
        elements.append(Paragraph(f"Data: {data_atual}", styles["Center"]))
        
        elements.append(Spacer(1, 5*mm))
        
        # Dados do mecânico e da carteira
        data = [
            ["Mecânico:", mecanico['nome']],
            ["Saldo Atual:", f"R$ {carteira['saldo']:.2f}".replace('.', ',')],
            ["Data Extrato:", data_atual],
        ]
        
        t = Table(data, colWidths=[25*mm, 45*mm])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 5*mm))
        
        # Tabela de movimentações
        if movimentacoes and len(movimentacoes) > 0:
            elements.append(Paragraph("<b>MOVIMENTAÇÕES FINANCEIRAS:</b>", styles["SmallNormal"]))
            
            # Cabeçalho da tabela
            data = [
                ["Data", "Valor", "Justificativa"]
            ]
            
            # Adicionar linhas de movimentações
            for mov in movimentacoes:
                try:
                    data_mov = datetime.fromisoformat(mov['data']).strftime('%d/%m/%Y')
                except:
                    data_mov = mov['data']
                
                valor = float(mov['valor'])
                justificativa = mov['justificativa']
                
                data.append([
                    data_mov,
                    f"R$ {valor:.2f}".replace('.', ','),
                    justificativa
                ])
            
            # Criar tabela
            col_widths = [15*mm, 15*mm, 40*mm]
            t = Table(data, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, 0), 0.5, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("Não existem movimentações para este período.", styles["SmallNormal"]))
        
        elements.append(Spacer(1, 10*mm))
        
        # Assinaturas
        elements.append(Paragraph("<b>CONFIRMAÇÃO DE RECEBIMENTO</b>", styles["Center"]))
        elements.append(Spacer(1, 10*mm))
        
        data = [
            ["_______________________", "_______________________"],
            ["Mecânico", "Responsável"],
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
        elements.append(Paragraph(f"Documento gerado em: {data_atual}", styles["Center"]))
        
        # Construir o documento
        doc.build(elements)
        
        return filepath