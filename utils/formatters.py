# -*- coding: utf-8 -*-

"""
Utilitários de formatação
Funções para formatar diversos tipos de dados para exibição.
"""

import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def format_currency(value):
    """
    Formata um valor monetário para exibição.
    
    Args:
        value (float): Valor monetário
        
    Returns:
        str: Valor formatado (ex: R$ 1.234,56)
    """
    try:
        # Formata o valor com separador de milhares e duas casas decimais
        formatted = f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao formatar valor monetário {value}: {e}")
        return "R$ 0,00"

def format_date(date_str):
    """
    Formata uma data no formato brasileiro (DD/MM/YYYY).
    
    Args:
        date_str (str): Data no formato YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD
        
    Returns:
        str: Data formatada (ex: 31/12/2023 14:30 ou 31/12/2023)
    """
    try:
        if not date_str:
            return ""
        
        # Detecta o formato da data
        if ' ' in date_str:  # Tem hora
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        else:  # Só data
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
            
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao formatar data {date_str}: {e}")
        return date_str

def format_phone(phone):
    """
    Formata um número de telefone.
    
    Args:
        phone (str): Número de telefone (ex: 69912345678)
        
    Returns:
        str: Telefone formatado (ex: (69) 91234-5678)
    """
    try:
        # Remove caracteres não numéricos
        phone = re.sub(r'[^\d]', '', phone)
        
        if not phone:
            return ""
        
        # Verifica o comprimento
        if len(phone) == 11:  # Celular com 9 dígitos
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
        elif len(phone) == 10:  # Telefone fixo
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        else:
            return phone  # Retorna sem formatação se não se encaixar nos padrões
            
    except Exception as e:
        logger.error(f"Erro ao formatar telefone {phone}: {e}")
        return phone

def format_percentage(value):
    """
    Formata uma porcentagem para exibição.
    
    Args:
        value (float): Valor percentual
        
    Returns:
        str: Porcentagem formatada (ex: 75%)
    """
    try:
        return f"{int(value)}%"
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao formatar porcentagem {value}: {e}")
        return "0%"

def text_to_uppercase(text):
    """
    Converte um texto para maiúsculas.
    
    Args:
        text (str): Texto a ser convertido
        
    Returns:
        str: Texto em maiúsculas
    """
    try:
        return text.upper()
    except (AttributeError, TypeError) as e:
        logger.error(f"Erro ao converter texto para maiúsculas: {e}")
        return text if text else ""

def limit_text_length(text, max_length, ellipsis=True):
    """
    Limita o comprimento de um texto.
    
    Args:
        text (str): Texto a ser limitado
        max_length (int): Comprimento máximo
        ellipsis (bool): Se True, adiciona "..." ao final de textos cortados
        
    Returns:
        str: Texto limitado
    """
    try:
        if not text:
            return ""
            
        if len(text) <= max_length:
            return text
            
        if ellipsis:
            return text[:max_length-3] + "..."
        else:
            return text[:max_length]
            
    except (TypeError, AttributeError) as e:
        logger.error(f"Erro ao limitar comprimento do texto: {e}")
        return text if text else ""

def clean_text(text):
    """
    Remove caracteres especiais e espaços extras de um texto.
    
    Args:
        text (str): Texto a ser limpo
        
    Returns:
        str: Texto limpo
    """
    try:
        if not text:
            return ""
            
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    except (TypeError, AttributeError) as e:
        logger.error(f"Erro ao limpar texto: {e}")
        return text if text else ""
