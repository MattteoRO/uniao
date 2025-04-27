from babel.numbers import format_decimal

def number_format(value, decimal_places=2, decimal_separator=',', thousands_separator='.'):
    """
    Formata um número para moeda brasileira
    
    Args:
        value (float): Valor a ser formatado
        decimal_places (int): Quantidade de casas decimais
        decimal_separator (str): Separador decimal
        thousands_separator (str): Separador de milhares
        
    Returns:
        str: Valor formatado
    """
    if value is None:
        return "0,00"
    
    try:
        value = float(value)
        return format_decimal(
            value, 
            format=f"#,##0.{'0' * decimal_places}", 
            locale='pt_BR'
        )
    except (ValueError, TypeError):
        return "0,00"

def abs_filter(value):
    """
    Retorna o valor absoluto de um número
    
    Args:
        value (float|int): Valor a ser transformado
        
    Returns:
        float|int: Valor absoluto
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0

def contains_text(value, text):
    """
    Verifica se um texto contém outro texto
    
    Args:
        value (str): Texto a ser verificado
        text (str): Texto a ser procurado
        
    Returns:
        bool: True se o texto contém o outro, False caso contrário
    """
    if value is None or text is None:
        return False
    
    return str(text).lower() in str(value).lower()

# Registre outros filtros personalizados aqui
def init_app(app):
    """
    Registra os filtros na aplicação Flask
    
    Args:
        app: Instância da aplicação Flask
    """
    app.jinja_env.filters['number_format'] = number_format
    app.jinja_env.filters['abs'] = abs_filter
    app.jinja_env.filters['contains_text'] = contains_text
    
    # Adicionar o teste 'search' para compatibilidade
    app.jinja_env.tests['search'] = lambda value, text: contains_text(value, text)