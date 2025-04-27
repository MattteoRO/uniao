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

# Registre outros filtros personalizados aqui
def init_app(app):
    """
    Registra os filtros na aplicação Flask
    
    Args:
        app: Instância da aplicação Flask
    """
    app.jinja_env.filters['number_format'] = number_format