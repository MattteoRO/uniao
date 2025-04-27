# -*- coding: utf-8 -*-

"""
Serviço de Carteira Digital
Fornece funcionalidades para gerenciar as carteiras digitais de mecânicos e da loja.
"""

import logging
from datetime import datetime

from database import execute_query
from models import Carteira

logger = logging.getLogger(__name__)

class CarteiraService:
    """
    Classe para gerenciar as carteiras digitais.
    Fornece métodos para consultar saldos, registrar movimentações e gerar extratos.
    """
    
    def __init__(self):
        """Inicializa o serviço de carteira digital."""
        pass
    
    def get_carteira_loja(self):
        """
        Obtém a carteira da loja.
        
        Returns:
            dict: Dados da carteira da loja
        """
        try:
            query = "SELECT * FROM carteiras WHERE tipo = 'loja' LIMIT 1"
            result = execute_query(query, fetch_one=True)
            
            if not result:
                # Cria a carteira da loja se não existir
                carteira_id = Carteira.create('loja')
                if carteira_id:
                    return self.get_carteira_by_id(carteira_id)
                return None
            
            return result
        except Exception as e:
            logger.error(f"Erro ao obter carteira da loja: {e}")
            return None
    
    def get_carteira_mecanico(self, mecanico_id):
        """
        Obtém a carteira de um mecânico.
        
        Args:
            mecanico_id (int): ID do mecânico
            
        Returns:
            dict: Dados da carteira do mecânico ou None se não existir
        """
        try:
            query = "SELECT * FROM carteiras WHERE tipo = 'mecanico' AND mecanico_id = ? LIMIT 1"
            result = execute_query(query, (mecanico_id,), fetch_one=True)
            
            if not result:
                # Cria a carteira do mecânico se não existir
                carteira_id = self.create_carteira_mecanico(mecanico_id)
                if carteira_id:
                    return self.get_carteira_by_id(carteira_id)
                return None
            
            return result
        except Exception as e:
            logger.error(f"Erro ao obter carteira do mecânico ID={mecanico_id}: {e}")
            return None
    
    def get_carteira_by_id(self, carteira_id):
        """
        Obtém uma carteira pelo ID.
        
        Args:
            carteira_id (int): ID da carteira
            
        Returns:
            dict: Dados da carteira ou None se não existir
        """
        try:
            query = """
                SELECT c.*, m.nome as mecanico_nome
                FROM carteiras c
                LEFT JOIN mecanicos m ON c.mecanico_id = m.id
                WHERE c.id = ?
            """
            
            result = execute_query(query, (carteira_id,), fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"Erro ao obter carteira ID={carteira_id}: {e}")
            return None
    
    def get_todas_carteiras(self):
        """
        Obtém todas as carteiras (loja e mecânicos).
        
        Returns:
            list: Lista de dicionários com dados das carteiras
        """
        try:
            query = """
                SELECT c.*, m.nome as mecanico_nome
                FROM carteiras c
                LEFT JOIN mecanicos m ON c.mecanico_id = m.id
                ORDER BY c.tipo DESC, m.nome
            """
            
            result = execute_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"Erro ao obter todas as carteiras: {e}")
            return []
    
    def get_extrato(self, carteira_id, data_inicio=None, data_fim=None):
        """
        Obtém o extrato de uma carteira.
        
        Args:
            carteira_id (int): ID da carteira
            data_inicio (str): Data inicial para filtro (formato: YYYY-MM-DD)
            data_fim (str): Data final para filtro (formato: YYYY-MM-DD)
            
        Returns:
            list: Lista de movimentações
        """
        try:
            query = """
                SELECT m.*, s.cliente
                FROM movimentacoes m
                LEFT JOIN servicos s ON m.servico_id = s.id
                WHERE m.carteira_id = ?
            """
            
            params = [carteira_id]
            
            if data_inicio:
                query += " AND DATE(m.data) >= DATE(?)"
                params.append(data_inicio)
            
            if data_fim:
                query += " AND DATE(m.data) <= DATE(?)"
                params.append(data_fim)
            
            query += " ORDER BY m.data DESC"
            
            result = execute_query(query, params, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"Erro ao obter extrato da carteira ID={carteira_id}: {e}")
            return []
    
    def registrar_movimentacao(self, carteira_id, valor, justificativa=None, servico_id=None):
        """
        Registra uma movimentação em uma carteira.
        
        Args:
            carteira_id (int): ID da carteira
            valor (float): Valor da movimentação (positivo para entrada, negativo para saída)
            justificativa (str): Justificativa para a movimentação (obrigatória para saídas)
            servico_id (int): ID do serviço relacionado (opcional)
            
        Returns:
            bool: True se a movimentação for registrada com sucesso
        """
        try:
            # Validações
            if valor == 0:
                raise ValueError("O valor da movimentação não pode ser zero.")
            
            if valor < 0 and not justificativa:
                raise ValueError("É necessário informar uma justificativa para saídas de valor.")
            
            # Obtém o saldo atual
            saldo_atual = Carteira.get_saldo(carteira_id)
            
            if saldo_atual is None:
                raise ValueError(f"Carteira ID={carteira_id} não encontrada.")
            
            # Verifica se há saldo suficiente para saídas
            if valor < 0 and (saldo_atual + valor) < 0:
                raise ValueError("Saldo insuficiente para esta operação.")
            
            # Insere a movimentação
            query = """
                INSERT INTO movimentacoes (carteira_id, valor, justificativa, data, servico_id)
                VALUES (?, ?, ?, ?, ?)
            """
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            execute_query(
                query, 
                (carteira_id, valor, justificativa, now, servico_id),
                commit=True
            )
            
            # Atualiza o saldo da carteira
            novo_saldo = saldo_atual + valor
            Carteira.update_saldo(carteira_id, novo_saldo)
            
            logger.info(f"Movimentação registrada: Carteira ID={carteira_id}, Valor={valor}, Novo Saldo={novo_saldo}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar movimentação: {e}")
            return False
    
    def create_carteira_mecanico(self, mecanico_id, saldo_inicial=0.0):
        """
        Cria uma carteira para um mecânico.
        
        Args:
            mecanico_id (int): ID do mecânico
            saldo_inicial (float): Saldo inicial da carteira
            
        Returns:
            int: ID da carteira criada ou None em caso de erro
        """
        try:
            # Verifica se o mecânico já tem uma carteira
            query = "SELECT id FROM carteiras WHERE tipo = 'mecanico' AND mecanico_id = ?"
            result = execute_query(query, (mecanico_id,), fetch_one=True)
            
            if result:
                logger.warning(f"Mecânico ID={mecanico_id} já possui uma carteira (ID={result['id']})")
                return result['id']
            
            # Cria a carteira
            carteira_id = Carteira.create('mecanico', mecanico_id, saldo_inicial)
            
            logger.info(f"Carteira criada para o mecânico ID={mecanico_id}: Carteira ID={carteira_id}")
            return carteira_id
            
        except Exception as e:
            logger.error(f"Erro ao criar carteira para mecânico ID={mecanico_id}: {e}")
            return None
    
    def get_resumo_carteiras(self):
        """
        Obtém um resumo dos saldos de todas as carteiras.
        
        Returns:
            dict: Dicionário com resumo dos saldos
        """
        try:
            # Saldo total da loja
            query_loja = """
                SELECT SUM(saldo) as saldo_total
                FROM carteiras 
                WHERE tipo = 'loja'
            """
            
            result_loja = execute_query(query_loja, fetch_one=True)
            saldo_loja = float(result_loja['saldo_total']) if result_loja and result_loja['saldo_total'] else 0.0
            
            # Saldo total dos mecânicos
            query_mecanicos = """
                SELECT SUM(saldo) as saldo_total
                FROM carteiras 
                WHERE tipo = 'mecanico'
            """
            
            result_mecanicos = execute_query(query_mecanicos, fetch_one=True)
            saldo_mecanicos = float(result_mecanicos['saldo_total']) if result_mecanicos and result_mecanicos['saldo_total'] else 0.0
            
            return {
                'saldo_loja': saldo_loja,
                'saldo_mecanicos': saldo_mecanicos,
                'saldo_total': saldo_loja + saldo_mecanicos
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo de carteiras: {e}")
            return {
                'saldo_loja': 0.0,
                'saldo_mecanicos': 0.0,
                'saldo_total': 0.0
            }