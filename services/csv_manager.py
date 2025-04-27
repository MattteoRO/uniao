"""
Gerenciador de CSV
Responsável por ler e manipular os dados do arquivo CSV de peças.
"""
import csv
import os
from flask import current_app


class CSVManager:
    """
    Classe que gerencia a leitura e manipulação do arquivo CSV de peças.
    """
    def __init__(self, caminho_csv='bdmonarkbd.csv'):
        """
        Inicializa o gerenciador CSV.
        
        Args:
            caminho_csv (str): Caminho para o arquivo CSV
        """
        self.caminho_csv = caminho_csv
        
    def obter_caminho_completo(self):
        """
        Retorna o caminho completo para o arquivo CSV.
        
        Returns:
            str: Caminho completo
        """
        # Usar o caminho raiz do projeto
        return os.path.join(os.getcwd(), self.caminho_csv)
    
    def buscar_pecas(self, termo_busca=None):
        """
        Busca peças no arquivo CSV, utilizando lógica específica baseada no termo de busca.
        
        Lógica:
        1. Se o termo tiver apenas números e até 6 dígitos: busca por ID exato
        2. Se o termo tiver letras ou combinação de letras/números: busca na DESCRICAO
        3. Se o termo tiver apenas números e mais de 8 dígitos: busca por CODBARRAS
        
        Args:
            termo_busca (str, optional): Termo para filtrar a busca
            
        Returns:
            list: Lista de peças encontradas
        """
        try:
            if not termo_busca:
                return []
                
            caminho = self.obter_caminho_completo()
            
            if not os.path.exists(caminho):
                return []
            
            # Determinar o tipo de busca
            termo_limpo = termo_busca.strip()
            busca_por_id = termo_limpo.isdigit() and len(termo_limpo) <= 6
            busca_por_codbarras = termo_limpo.isdigit() and len(termo_limpo) >= 8
            busca_por_descricao = not (busca_por_id or busca_por_codbarras)
            
            pecas = []
            with open(caminho, 'r', encoding='utf-8-sig') as arquivo:
                leitor = csv.DictReader(arquivo)
                for linha in leitor:
                    adicionar_peca = False
                    
                    # Aplicar a lógica de busca conforme o tipo
                    if busca_por_id and linha.get('ID', '') == termo_limpo:
                        adicionar_peca = True
                    elif busca_por_codbarras and linha.get('CODBARRAS', '') == termo_limpo:
                        adicionar_peca = True
                    elif busca_por_descricao and termo_limpo.lower() in linha.get('DESCRICAO', '').lower():
                        adicionar_peca = True
                    
                    if adicionar_peca:
                        # Tratar preço: substituir "," por "." e converter para float
                        preco_str = linha.get('PRECOVENDA', '0')
                        preco_str = preco_str.replace('.', '').replace(',', '.')
                        try:
                            preco = float(preco_str)
                        except ValueError:
                            preco = 0.0
                        
                        peca = {
                            'id': linha.get('ID', ''),
                            'descricao': linha.get('DESCRICAO', ''),
                            'preco': preco,
                            'codigo_barras': linha.get('CODBARRAS', '') if linha.get('CODBARRAS', 'NULL') != 'NULL' else ''
                        }
                        pecas.append(peca)
            
            return pecas
        except Exception as e:
            print(f"Erro ao ler arquivo CSV: {e}")
            return []
    
    def buscar_peca_por_id(self, peca_id):
        """
        Busca uma peça específica por ID.
        
        Args:
            peca_id (str): ID da peça
            
        Returns:
            dict: Dados da peça ou None se não encontrada
        """
        pecas = self.buscar_pecas()
        for peca in pecas:
            if peca['id'] == peca_id:
                return peca
        return None
    
    def buscar_peca_por_codigo_barras(self, codigo_barras):
        """
        Busca uma peça específica por código de barras.
        
        Args:
            codigo_barras (str): Código de barras da peça
            
        Returns:
            dict: Dados da peça ou None se não encontrada
        """
        pecas = self.buscar_pecas()
        for peca in pecas:
            if peca['codigo_barras'] == codigo_barras:
                return peca
        return None
    
    @staticmethod
    def csv_para_lista(caminho_csv):
        """
        Converte um arquivo CSV para uma lista de dicionários.
        
        Args:
            caminho_csv (str): Caminho para o arquivo CSV
            
        Returns:
            list: Lista de dicionários representando as linhas do CSV
        """
        try:
            with open(caminho_csv, 'r', encoding='utf-8-sig') as arquivo:
                leitor = csv.DictReader(arquivo)
                return list(leitor)
        except Exception as e:
            print(f"Erro ao converter CSV para lista: {e}")
            return []