# -*- coding: utf-8 -*-

"""
Gerenciador de CSV
Responsável por carregar, pesquisar e atualizar o arquivo CSV de peças.
"""

import os
import csv
import logging
import re

logger = logging.getLogger(__name__)

class CSVManager:
    """
    Classe para gerenciar o arquivo CSV de peças.
    """
    
    def __init__(self, csv_path="bdmonarkbd.csv"):
        """
        Inicializa o gerenciador de CSV.
        
        Args:
            csv_path (str): Caminho para o arquivo CSV
        """
        self.csv_path = csv_path
    
    def _validate_csv(self):
        """
        Verifica se o arquivo CSV existe e possui o formato correto.
        
        Returns:
            bool: True se o arquivo é válido, False caso contrário
        """
        if not os.path.isfile(self.csv_path):
            logger.error(f"Arquivo CSV não encontrado: {self.csv_path}")
            return False
        
        try:
            # Verifica se o arquivo pode ser aberto e possui as colunas esperadas
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Verifica as colunas obrigatórias
                required_columns = ["ID", "DESCRICAO", "PRECOVENDA", "CODBARRAS"]
                
                # Verifica se todas as colunas obrigatórias estão presentes
                if not all(col in header for col in required_columns):
                    logger.error(f"Formato de CSV inválido. Colunas esperadas: {required_columns}, encontradas: {header}")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Erro ao validar o arquivo CSV: {e}")
            return False
    
    def _parse_price(self, price_str):
        """
        Converte uma string de preço para float.
        
        Args:
            price_str (str): String de preço (ex: "1.700,00" ou "1,00")
            
        Returns:
            float: Valor convertido para float
        """
        try:
            # Remove aspas se presentes
            price_str = price_str.strip('"\'')
            
            # Substitui separadores para o formato numérico
            # "1.700,00" ou "1,00" -> 1700.00 ou 1.00
            # Remove pontos (separadores de milhar) e substitui vírgula por ponto
            price_str = price_str.replace('.', '').replace(',', '.')
            
            return float(price_str)
        except (ValueError, AttributeError) as e:
            logger.error(f"Erro ao converter preço '{price_str}': {e}")
            return 0.0
    
    def _format_price(self, price_float):
        """
        Formata um preço float para o formato do CSV.
        
        Args:
            price_float (float): Valor do preço
            
        Returns:
            str: Preço formatado como string (ex: "1.700,00" ou "1,00")
        """
        try:
            # Formata para o padrão brasileiro (com vírgula como separador decimal)
            integer_part = int(price_float)
            decimal_part = int(round((price_float - integer_part) * 100))
            
            # Formata com separador de milhares (ponto) a cada 3 dígitos
            integer_str = f"{integer_part:,}".replace(',', '.')
            
            # Adiciona zeros à esquerda na parte decimal se necessário
            decimal_str = f"{decimal_part:02d}"
            
            return f"{integer_str},{decimal_str}"
        except Exception as e:
            logger.error(f"Erro ao formatar preço {price_float}: {e}")
            return "0,00"
    
    def search_parts(self, search_term):
        """
        Pesquisa peças no arquivo CSV.
        
        Args:
            search_term (str): Termo de pesquisa
            
        Returns:
            list: Lista de peças encontradas
        """
        if not self._validate_csv():
            raise ValueError("Arquivo CSV inválido ou não encontrado")
        
        results = []
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Determina o tipo de pesquisa
                search_type = self._determine_search_type(search_term)
                
                # Realiza a pesquisa
                for row in reader:
                    if search_type == "id":
                        # Pesquisa por ID
                        if row["ID"] == search_term:
                            results.append(row)
                            break  # ID é único, então podemos parar após encontrá-lo
                            
                    elif search_type == "description":
                        # Pesquisa por descrição (insensível a maiúsculas/minúsculas)
                        if search_term.upper() in row["DESCRICAO"].upper():
                            results.append(row)
                            
                    elif search_type == "barcode":
                        # Pesquisa por código de barras
                        if row["CODBARRAS"] != "NULL" and row["CODBARRAS"] == search_term:
                            results.append(row)
                            break  # Código de barras é único, então podemos parar após encontrá-lo
        
        except Exception as e:
            logger.error(f"Erro ao pesquisar peças: {e}")
            raise
        
        return results
    
    def _determine_search_type(self, search_term):
        """
        Determina o tipo de pesquisa com base no termo digitado.
        
        Args:
            search_term (str): Termo de pesquisa
            
        Returns:
            str: Tipo de pesquisa ("id", "description" ou "barcode")
        """
        # Verifica se é apenas números
        if re.match(r'^\d+$', search_term):
            # Verifica o comprimento
            if len(search_term) <= 6:
                return "id"
            elif len(search_term) >= 8:
                return "barcode"
        
        # Se não se encaixa nos casos acima, é uma pesquisa por descrição
        return "description"
    
    def update_part_price(self, part_id, new_price):
        """
        Atualiza o preço de uma peça no arquivo CSV.
        
        Args:
            part_id (int): ID da peça
            new_price (float): Novo preço da peça
            
        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário
        """
        if not self._validate_csv():
            raise ValueError("Arquivo CSV inválido ou não encontrado")
        
        # Converte o ID para string para comparação
        part_id_str = str(part_id)
        
        try:
            # Lê todo o CSV
            rows = []
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames
                
                for row in reader:
                    if row["ID"] == part_id_str:
                        # Atualiza o preço
                        row["PRECOVENDA"] = f'"{self._format_price(new_price)}"'
                    rows.append(row)
            
            # Escreve o CSV atualizado
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"Preço da peça ID={part_id} atualizado para {new_price}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar preço da peça: {e}")
            raise
