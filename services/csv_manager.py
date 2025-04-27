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
        1. Se o termo tiver apenas números: busca por ID exato em toda a coluna ID
        2. Se o termo tiver letras ou combinação de letras/números: busca na DESCRICAO
        3. Se o termo incluir código de barras: busca por CODBARRAS
        
        Args:
            termo_busca (str, optional): Termo para filtrar a busca
            
        Returns:
            list: Lista de peças encontradas
        """
        try:
            caminho = self.obter_caminho_completo()
            if not os.path.exists(caminho):
                print(f"Arquivo CSV não encontrado: {caminho}")
                return []
                
            if not termo_busca:
                # Retorna as primeiras 50 peças se não houver termo
                pecas = []
                count = 0
                with open(caminho, 'r', encoding='utf-8-sig') as arquivo:
                    leitor = csv.DictReader(arquivo)
                    for linha in leitor:
                        if count >= 50:
                            break
                            
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
                        count += 1
                return pecas
                
            # Determinar o tipo de busca
            termo_limpo = termo_busca.strip()
            busca_por_id = termo_limpo.isdigit()  # Qualquer número é considerado possível ID
            busca_por_descricao = not termo_limpo.isdigit()  # Se não for apenas números, busca por descrição
            
            pecas = []
            with open(caminho, 'r', encoding='utf-8-sig') as arquivo:
                leitor = csv.DictReader(arquivo)
                for linha in leitor:
                    adicionar_peca = False
                    
                    # Aplicar a lógica de busca conforme o tipo
                    if busca_por_id:
                        # Verificar se o ID contém o termo de busca (busca parcial por ID)
                        id_peca = linha.get('ID', '')
                        if termo_limpo in id_peca:
                            adicionar_peca = True
                        # Verificar se o código de barras coincide (busca exata por código de barras)
                        elif linha.get('CODBARRAS', '') == termo_limpo:
                            adicionar_peca = True
                    
                    # Busca por descrição (mesmo se já encontrou por ID)
                    if busca_por_descricao and termo_limpo.lower() in linha.get('DESCRICAO', '').lower():
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