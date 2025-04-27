# -*- coding: utf-8 -*-

"""
Modelos de dados
Define as estruturas de dados utilizadas no sistema.
"""

import json
import logging
import sqlite3
from datetime import datetime

from database import execute_query

logger = logging.getLogger(__name__)

class Carteira:
    """
    Classe que representa uma carteira digital.
    Pode pertencer a um mecânico ou à loja.
    """
    
    @staticmethod
    def get_by_id(carteira_id):
        """
        Obtém uma carteira pelo ID.
        
        Args:
            carteira_id (int): ID da carteira
            
        Returns:
            dict: Dados da carteira ou None se não existir
        """
        try:
            query = "SELECT * FROM carteiras WHERE id = ?"
            result = execute_query(query, (carteira_id,), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Erro ao obter carteira por ID: {e}")
            return None
    
    @staticmethod
    def create(tipo, mecanico_id=None, saldo_inicial=0.0):
        """
        Cria uma nova carteira.
        
        Args:
            tipo (str): Tipo da carteira ('mecanico' ou 'loja')
            mecanico_id (int, optional): ID do mecânico (apenas para tipo 'mecanico')
            saldo_inicial (float, optional): Saldo inicial da carteira
            
        Returns:
            int: ID da carteira criada ou None em caso de erro
        """
        try:
            query = """
                INSERT INTO carteiras (tipo, mecanico_id, saldo)
                VALUES (?, ?, ?)
            """
            
            execute_query(
                query, 
                (tipo, mecanico_id, saldo_inicial),
                commit=True
            )
            
            # Obtém o ID da carteira inserida
            carteira_id = execute_query(
                "SELECT last_insert_rowid()", 
                fetch_one=True
            )
            
            logger.info(f"Carteira criada: ID={carteira_id[0]}, Tipo={tipo}")
            return carteira_id[0] if carteira_id else None
        except Exception as e:
            logger.error(f"Erro ao criar carteira: {e}")
            return None
    
    @staticmethod
    def get_saldo(carteira_id):
        """
        Obtém o saldo atual de uma carteira.
        
        Args:
            carteira_id (int): ID da carteira
            
        Returns:
            float: Saldo da carteira ou None em caso de erro
        """
        try:
            query = "SELECT saldo FROM carteiras WHERE id = ?"
            result = execute_query(query, (carteira_id,), fetch_one=True)
            return float(result['saldo']) if result else None
        except Exception as e:
            logger.error(f"Erro ao obter saldo da carteira: {e}")
            return None
    
    @staticmethod
    def update_saldo(carteira_id, novo_saldo):
        """
        Atualiza o saldo de uma carteira.
        
        Args:
            carteira_id (int): ID da carteira
            novo_saldo (float): Novo saldo
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        try:
            query = """
                UPDATE carteiras
                SET saldo = ?
                WHERE id = ?
            """
            
            execute_query(
                query, 
                (novo_saldo, carteira_id),
                commit=True
            )
            
            logger.info(f"Saldo da carteira ID={carteira_id} atualizado para {novo_saldo}")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar saldo da carteira: {e}")
            return False


class Mecanico:
    """
    Classe que representa um mecânico.
    Pode ter uma carteira digital associada.
    """
    
    @staticmethod
    def get_all(include_inactive=False):
        """
        Obtém todos os mecânicos cadastrados.
        
        Args:
            include_inactive (bool): Se True, inclui mecânicos inativos
            
        Returns:
            list: Lista de dicionários com dados dos mecânicos
        """
        try:
            query = "SELECT * FROM mecanicos"
            if not include_inactive:
                query += " WHERE ativo = 1"
            query += " ORDER BY nome"
            
            result = execute_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"Erro ao obter mecânicos: {e}")
            return []
    
    @staticmethod
    def get_by_id(mecanico_id):
        """
        Obtém um mecânico pelo ID.
        
        Args:
            mecanico_id (int): ID do mecânico
            
        Returns:
            dict: Dados do mecânico ou None se não existir
        """
        try:
            query = "SELECT * FROM mecanicos WHERE id = ?"
            result = execute_query(query, (mecanico_id,), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Erro ao obter mecânico por ID: {e}")
            return None
    
    @staticmethod
    def create(nome, telefone=None):
        """
        Cria um novo mecânico.
        
        Args:
            nome (str): Nome do mecânico
            telefone (str, optional): Telefone do mecânico
            
        Returns:
            int: ID do mecânico criado ou None em caso de erro
        """
        try:
            query = """
                INSERT INTO mecanicos (nome, telefone, ativo, data_cadastro)
                VALUES (?, ?, 1, ?)
            """
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = execute_query(
                query, 
                (nome, telefone, now),
                commit=True
            )
            
            # Obtém o ID do mecânico inserido
            mecanico_id = execute_query(
                "SELECT last_insert_rowid()", 
                fetch_one=True
            )
            
            if mecanico_id:
                # Cria uma carteira digital para o mecânico
                from services.carteira_service import CarteiraService
                carteira_service = CarteiraService()
                carteira_service.create_carteira_mecanico(mecanico_id[0])
                
                logger.info(f"Mecânico criado: ID={mecanico_id[0]}, Nome={nome}")
                return mecanico_id[0]
            
            return None
        except Exception as e:
            logger.error(f"Erro ao criar mecânico: {e}")
            return None
    
    @staticmethod
    def update(mecanico_id, nome, telefone=None):
        """
        Atualiza os dados de um mecânico.
        
        Args:
            mecanico_id (int): ID do mecânico
            nome (str): Nome do mecânico
            telefone (str, optional): Telefone do mecânico
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        try:
            query = """
                UPDATE mecanicos
                SET nome = ?, telefone = ?
                WHERE id = ?
            """
            
            execute_query(
                query, 
                (nome, telefone, mecanico_id),
                commit=True
            )
            
            logger.info(f"Mecânico atualizado: ID={mecanico_id}, Nome={nome}")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar mecânico: {e}")
            return False
    
    @staticmethod
    def deactivate(mecanico_id):
        """
        Desativa um mecânico (exclusão lógica).
        
        Args:
            mecanico_id (int): ID do mecânico
            
        Returns:
            bool: True se a desativação foi bem-sucedida
        """
        try:
            query = """
                UPDATE mecanicos
                SET ativo = 0
                WHERE id = ?
            """
            
            execute_query(query, (mecanico_id,), commit=True)
            
            logger.info(f"Mecânico desativado: ID={mecanico_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao desativar mecânico: {e}")
            return False
    
    @staticmethod
    def activate(mecanico_id):
        """
        Ativa um mecânico.
        
        Args:
            mecanico_id (int): ID do mecânico
            
        Returns:
            bool: True se a ativação foi bem-sucedida
        """
        try:
            query = """
                UPDATE mecanicos
                SET ativo = 1
                WHERE id = ?
            """
            
            execute_query(query, (mecanico_id,), commit=True)
            
            logger.info(f"Mecânico ativado: ID={mecanico_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao ativar mecânico: {e}")
            return False


class Servico:
    """
    Classe que representa um serviço.
    """
    
    def __init__(self):
        """Inicializa um novo serviço."""
        self.id = None
        self.cliente = ""
        self.telefone = ""
        self.descricao = ""
        self.mecanico_id = None
        self.valor_servico = 0.0
        self.porcentagem_mecanico = 0
        self.data_criacao = datetime.now()
        self.status = "aberto"  # aberto, concluido, cancelado
        self.pecas = []  # Lista de peças usadas no serviço
    
    def adicionar_peca(self, peca_id, descricao, preco_unitario, quantidade, codigo_barras=None):
        """
        Adiciona uma peça ao serviço.
        
        Args:
            peca_id (str): ID da peça
            descricao (str): Descrição da peça
            preco_unitario (float): Preço unitário da peça
            quantidade (int): Quantidade da peça
            codigo_barras (str, optional): Código de barras da peça
        """
        peca = {
            'id': peca_id,
            'descricao': descricao,
            'preco_unitario': preco_unitario,
            'quantidade': quantidade,
            'codigo_barras': codigo_barras
        }
        
        # Verifica se a peça já existe na lista
        for idx, p in enumerate(self.pecas):
            if p['id'] == peca_id:
                # Atualiza a peça existente
                self.pecas[idx] = peca
                return
        
        # Adiciona nova peça
        self.pecas.append(peca)
    
    def remover_peca(self, peca_id):
        """
        Remove uma peça do serviço.
        
        Args:
            peca_id (str): ID da peça a ser removida
            
        Returns:
            bool: True se a peça foi removida, False caso contrário
        """
        for idx, peca in enumerate(self.pecas):
            if peca['id'] == peca_id:
                self.pecas.pop(idx)
                return True
        
        return False
    
    def get_valor_total_pecas(self):
        """
        Calcula o valor total das peças do serviço.
        
        Returns:
            float: Valor total das peças
        """
        total = 0.0
        for peca in self.pecas:
            preco = float(peca['preco_unitario'])
            quantidade = int(peca['quantidade'])
            total += preco * quantidade
        
        return total
    
    def get_valor_total(self):
        """
        Calcula o valor total do serviço (mão de obra + peças).
        
        Returns:
            float: Valor total do serviço
        """
        return self.valor_servico + self.get_valor_total_pecas()
    
    def get_valor_mecanico(self):
        """
        Calcula o valor destinado ao mecânico.
        
        Returns:
            float: Valor destinado ao mecânico
        """
        return self.valor_servico * (self.porcentagem_mecanico / 100)
    
    def get_valor_loja(self):
        """
        Calcula o valor destinado à loja (mão de obra + peças).
        
        Returns:
            float: Valor destinado à loja
        """
        valor_mecanico = self.get_valor_mecanico()
        return (self.valor_servico - valor_mecanico) + self.get_valor_total_pecas()
    
    def save(self):
        """
        Salva o serviço no banco de dados.
        
        Returns:
            int: ID do serviço ou None em caso de erro
        """
        try:
            # Se for um serviço existente
            if self.id is not None:
                query = """
                    UPDATE servicos
                    SET cliente = ?, telefone = ?, descricao = ?, mecanico_id = ?,
                        valor_servico = ?, porcentagem_mecanico = ?, status = ?
                    WHERE id = ?
                """
                
                execute_query(
                    query,
                    (
                        self.cliente, self.telefone, self.descricao, self.mecanico_id,
                        self.valor_servico, self.porcentagem_mecanico, self.status,
                        self.id
                    ),
                    commit=True
                )
                
                # Limpa as peças existentes
                execute_query(
                    "DELETE FROM servico_pecas WHERE servico_id = ?",
                    (self.id,),
                    commit=True
                )
                
            else:
                # Novo serviço
                query = """
                    INSERT INTO servicos (
                        cliente, telefone, descricao, mecanico_id,
                        valor_servico, porcentagem_mecanico, data_criacao, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                execute_query(
                    query,
                    (
                        self.cliente, self.telefone, self.descricao, self.mecanico_id,
                        self.valor_servico, self.porcentagem_mecanico, now, self.status
                    ),
                    commit=True
                )
                
                # Obtém o ID do serviço inserido
                servico_id = execute_query(
                    "SELECT last_insert_rowid()",
                    fetch_one=True
                )
                
                if servico_id:
                    self.id = servico_id[0]
                    self.data_criacao = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
                else:
                    raise Exception("Erro ao obter ID do serviço inserido")
            
            # Insere as peças
            for peca in self.pecas:
                query = """
                    INSERT INTO servico_pecas (
                        servico_id, peca_id, descricao, preco_unitario,
                        quantidade, codigo_barras
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                
                execute_query(
                    query,
                    (
                        self.id, peca['id'], peca['descricao'], peca['preco_unitario'],
                        peca['quantidade'], peca.get('codigo_barras')
                    ),
                    commit=True
                )
            
            # Registra os valores na carteira do mecânico e da loja
            if self.status == "concluido":
                self._registrar_movimentacoes()
            
            logger.info(f"Serviço salvo: ID={self.id}, Cliente={self.cliente}")
            return self.id
            
        except Exception as e:
            logger.error(f"Erro ao salvar serviço: {e}")
            return None
    
    def _registrar_movimentacoes(self):
        """Registra as movimentações financeiras nas carteiras."""
        try:
            from services.carteira_service import CarteiraService
            
            carteira_service = CarteiraService()
            
            # Obtém as carteiras
            carteira_loja = carteira_service.get_carteira_loja()
            carteira_mecanico = carteira_service.get_carteira_mecanico(self.mecanico_id)
            
            if not carteira_loja or not carteira_mecanico:
                logger.error("Carteiras não encontradas")
                return False
            
            # Registra o valor na carteira do mecânico
            valor_mecanico = self.get_valor_mecanico()
            if valor_mecanico > 0:
                carteira_service.registrar_movimentacao(
                    carteira_mecanico['id'],
                    valor_mecanico,
                    f"Serviço #{self.id} - {self.porcentagem_mecanico}% da mão de obra",
                    self.id
                )
            
            # Registra o valor na carteira da loja
            valor_loja = self.get_valor_loja()
            if valor_loja > 0:
                carteira_service.registrar_movimentacao(
                    carteira_loja['id'],
                    valor_loja,
                    f"Serviço #{self.id} - {100 - self.porcentagem_mecanico}% da mão de obra + peças",
                    self.id
                )
            
            return True
        
        except Exception as e:
            logger.error(f"Erro ao registrar movimentações: {e}")
            return False
    
    @staticmethod
    def get_all(filtros=None):
        """
        Obtém todos os serviços cadastrados.
        
        Args:
            filtros (dict, optional): Filtros para a consulta
                Chaves possíveis:
                - status: Status dos serviços ("aberto", "concluido", "cancelado")
                - cliente: Nome do cliente (pesquisa parcial)
                - data_inicio: Data inicial (formato: "YYYY-MM-DD")
                - data_fim: Data final (formato: "YYYY-MM-DD")
                - mecanico_id: ID do mecânico
            
        Returns:
            list: Lista de serviços
        """
        try:
            query = """
                SELECT s.*, m.nome as mecanico_nome
                FROM servicos s
                LEFT JOIN mecanicos m ON s.mecanico_id = m.id
            """
            
            params = []
            where_clauses = []
            
            if filtros:
                if 'status' in filtros and filtros['status']:
                    where_clauses.append("s.status = ?")
                    params.append(filtros['status'])
                
                if 'cliente' in filtros and filtros['cliente']:
                    where_clauses.append("s.cliente LIKE ?")
                    params.append(f"%{filtros['cliente']}%")
                
                if 'data_inicio' in filtros and filtros['data_inicio']:
                    where_clauses.append("DATE(s.data_criacao) >= DATE(?)")
                    params.append(filtros['data_inicio'])
                
                if 'data_fim' in filtros and filtros['data_fim']:
                    where_clauses.append("DATE(s.data_criacao) <= DATE(?)")
                    params.append(filtros['data_fim'])
                
                if 'mecanico_id' in filtros and filtros['mecanico_id']:
                    where_clauses.append("s.mecanico_id = ?")
                    params.append(filtros['mecanico_id'])
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " ORDER BY s.data_criacao DESC"
            
            servicos = execute_query(query, params, fetch_all=True)
            
            # Adiciona as peças a cada serviço
            for servico in servicos:
                servico_id = servico['id']
                
                query_pecas = """
                    SELECT * FROM servico_pecas
                    WHERE servico_id = ?
                """
                
                pecas = execute_query(query_pecas, (servico_id,), fetch_all=True)
                servico['pecas'] = pecas
                
                # Calcular valores totais
                valor_total_pecas = sum(float(p['preco_unitario']) * int(p['quantidade']) for p in pecas)
                servico['valor_total_pecas'] = valor_total_pecas
                servico['valor_total'] = float(servico['valor_servico']) + valor_total_pecas
            
            return servicos
            
        except Exception as e:
            logger.error(f"Erro ao obter serviços: {e}")
            return []
    
    @staticmethod
    def get_by_id(servico_id):
        """
        Obtém um serviço pelo ID.
        
        Args:
            servico_id (int): ID do serviço
            
        Returns:
            Servico: Instância do serviço ou None se não existir
        """
        try:
            query = """
                SELECT s.*, m.nome as mecanico_nome
                FROM servicos s
                LEFT JOIN mecanicos m ON s.mecanico_id = m.id
                WHERE s.id = ?
            """
            
            result = execute_query(query, (servico_id,), fetch_one=True)
            
            if not result:
                return None
            
            servico = Servico()
            servico.id = result['id']
            servico.cliente = result['cliente']
            servico.telefone = result['telefone']
            servico.descricao = result['descricao']
            servico.mecanico_id = result['mecanico_id']
            servico.valor_servico = float(result['valor_servico'])
            servico.porcentagem_mecanico = int(result['porcentagem_mecanico'])
            servico.data_criacao = datetime.strptime(result['data_criacao'], "%Y-%m-%d %H:%M:%S")
            servico.status = result['status']
            
            # Carrega as peças
            query_pecas = """
                SELECT * FROM servico_pecas
                WHERE servico_id = ?
            """
            
            pecas = execute_query(query_pecas, (servico_id,), fetch_all=True)
            
            for peca in pecas:
                servico.adicionar_peca(
                    peca['peca_id'],
                    peca['descricao'],
                    float(peca['preco_unitario']),
                    int(peca['quantidade']),
                    peca['codigo_barras']
                )
            
            return servico
            
        except Exception as e:
            logger.error(f"Erro ao obter serviço por ID: {e}")
            return None
    
    @staticmethod
    def concluir(servico_id):
        """
        Conclui um serviço.
        
        Args:
            servico_id (int): ID do serviço
            
        Returns:
            bool: True se o serviço foi concluído
        """
        try:
            # Obtém o serviço
            servico = Servico.get_by_id(servico_id)
            
            if not servico:
                return False
            
            servico.status = "concluido"
            servico.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao concluir serviço: {e}")
            return False
    
    @staticmethod
    def cancelar(servico_id):
        """
        Cancela um serviço.
        
        Args:
            servico_id (int): ID do serviço
            
        Returns:
            bool: True se o serviço foi cancelado
        """
        try:
            query = """
                UPDATE servicos
                SET status = 'cancelado'
                WHERE id = ?
            """
            
            execute_query(query, (servico_id,), commit=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao cancelar serviço: {e}")
            return False


class Configuracao:
    """
    Classe para gerenciar as configurações do sistema.
    """
    
    @staticmethod
    def get():
        """
        Obtém as configurações atuais.
        
        Returns:
            dict: Configurações ou None se não existirem
        """
        try:
            query = "SELECT * FROM configuracoes LIMIT 1"
            result = execute_query(query, fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Erro ao obter configurações: {e}")
            return None
    
    @staticmethod
    def update(nome_empresa, endereco=None, telefone=None, caminho_csv="bdmonarkbd.csv"):
        """
        Atualiza as configurações.
        
        Args:
            nome_empresa (str): Nome da empresa
            endereco (str, optional): Endereço da empresa
            telefone (str, optional): Telefone da empresa
            caminho_csv (str, optional): Caminho para o arquivo CSV de peças
            
        Returns:
            bool: True se a atualização foi bem-sucedida
        """
        try:
            # Verifica se já existe uma configuração
            config = Configuracao.get()
            
            if config:
                # Atualiza a configuração existente
                query = """
                    UPDATE configuracoes
                    SET nome_empresa = ?, endereco = ?, telefone = ?, caminho_csv = ?
                """
            else:
                # Cria uma nova configuração
                query = """
                    INSERT INTO configuracoes
                    (nome_empresa, endereco, telefone, caminho_csv)
                    VALUES (?, ?, ?, ?)
                """
            
            execute_query(
                query, 
                (nome_empresa, endereco, telefone, caminho_csv),
                commit=True
            )
            
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações: {e}")
            return False