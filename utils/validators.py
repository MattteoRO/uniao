# -*- coding: utf-8 -*-

"""
Utilitários de validação
Funções para validar diversos tipos de entrada de dados.
"""

import re
import logging

logger = logging.getLogger(__name__)

def validate_phone(phone):
    """
    Valida um número de telefone.
    Formato válido: DDD + número (8 ou 9 dígitos)
    Exemplo: 69912345678
    
    Args:
        phone (str): Número de telefone a ser validado
        
    Returns:
        tuple: (bool, str) - (Válido, Mensagem de erro ou sucesso)
    """
    # Remove espaços, traços e parênteses
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Verifica se só contém dígitos
    if not phone.isdigit():
        return False, "O telefone deve conter apenas números"
    
    # Verifica o comprimento (10 ou 11 dígitos)
    length = len(phone)
    if length < 10 or length > 11:
        return False, "O telefone deve ter entre 10 e 11 dígitos (DDD + número)"
    
    # Extrai DDD e número
    ddd = phone[:2]
    numero = phone[2:]
    
    # Verifica o DDD
    if ddd == "00":
        return False, "DDD inválido"
    
    # Verifica o número (para celular deve começar com 9)
    if len(numero) == 9 and numero[0] != '9':
        return False, "Número de celular deve começar com 9"
    
    return True, "Telefone válido"

def validate_money(value):
    """
    Valida um valor monetário.
    Aceita números positivos com até duas casas decimais.
    
    Args:
        value (str): Valor monetário a ser validado
        
    Returns:
        tuple: (bool, str) - (Válido, Mensagem de erro ou sucesso)
    """
    # Remove espaços
    value = value.strip()
    
    # Verifica se está vazio
    if not value:
        return False, "O valor não pode estar vazio"
    
    # Tenta converter para float
    try:
        value_float = float(value)
    except ValueError:
        return False, "O valor deve ser um número"
    
    # Verifica se é positivo
    if value_float < 0:
        return False, "O valor não pode ser negativo"
    
    # Verifica o número de casas decimais
    if '.' in value:
        integer, decimal = value.split('.')
        if len(decimal) > 2:
            return False, "O valor deve ter no máximo duas casas decimais"
    
    return True, "Valor válido"

def validate_percentage(value):
    """
    Valida uma porcentagem.
    Aceita números inteiros de 0 a 100.
    
    Args:
        value (str): Valor percentual a ser validado
        
    Returns:
        tuple: (bool, str) - (Válido, Mensagem de erro ou sucesso)
    """
    # Remove espaços
    value = value.strip()
    
    # Verifica se está vazio
    if not value:
        return False, "A porcentagem não pode estar vazia"
    
    # Verifica se é um número inteiro
    if not value.isdigit():
        return False, "A porcentagem deve ser um número inteiro"
    
    # Converte para inteiro
    value_int = int(value)
    
    # Verifica o intervalo
    if value_int < 0 or value_int > 100:
        return False, "A porcentagem deve estar entre 0 e 100"
    
    return True, "Porcentagem válida"

def validate_required_field(value, field_name):
    """
    Valida se um campo obrigatório foi preenchido.
    
    Args:
        value (str): Valor do campo
        field_name (str): Nome do campo para mensagem de erro
        
    Returns:
        tuple: (bool, str) - (Válido, Mensagem de erro ou sucesso)
    """
    if not value or value.strip() == "":
        return False, f"O campo {field_name} é obrigatório"
    
    return True, f"Campo {field_name} válido"

def validate_date_format(date_str):
    """
    Valida o formato de uma data (YYYY-MM-DD).
    
    Args:
        date_str (str): String de data para validar
        
    Returns:
        tuple: (bool, str) - (Válido, Mensagem de erro ou sucesso)
    """
    import re
    from datetime import datetime
    
    # Verifica se está vazio
    if not date_str or date_str.strip() == "":
        return False, "A data não pode estar vazia"
    
    # Padrão YYYY-MM-DD
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    if not re.match(pattern, date_str):
        return False, "O formato da data deve ser AAAA-MM-DD"
    
    # Valida se é uma data válida
    try:
        year, month, day = map(int, date_str.split('-'))
        datetime(year, month, day)
        return True, "Data válida"
    except ValueError:
        return False, "Data inválida"
