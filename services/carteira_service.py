# -*- coding: utf-8 -*-

"""
Serviço de Carteira Digital
Fornece funcionalidades para gerenciar as carteiras digitais de mecânicos e da loja.
"""

import logging
from datetime import datetime

from models import Carteira, Mecanico
from utils.formatters import format_currency, format_date

logger = logging.getLogger(__name__)

class CarteiraService:
    """
    Classe para gerenciar as carteiras digitais.
    Fornece métodos para consultar saldos, registrar movimentações e gerar extratos.
    """
    
    def __init__(self):
        """Inicializa o serviço de carteira digital."""
        logger.debug("Serviço de carteira digital inicializado")
    
    def get_carteira_loja(self):
        """
        Obtém a carteira da loja.
        
        Returns:
            dict: Dados da carteira da loja
        """
        try:
            carteira = Carteira.get_loja_carteira()
            
            if not carteira:
                # Se não existir, cria a carteira da loja
                logger.warning("Carteira da loja não encontrada, criando uma nova")
                carteira_obj = Carteira(tipo='loja', mecanico_id=None, saldo=0.0)
                carteira_obj.save()
                carteira = Carteira.get_loja_carteira()
                
            return carteira
            
        except Exception as e:
            logger.error(f"Erro ao obter carteira da loja: {e}")
            raise
    
    def get_carteira_mecanico(self, mecanico_id):
        """
        Obtém a carteira de um mecânico.
        
        Args:
            mecanico_id (int): ID do mecânico
            
        Returns:
            dict: Dados da carteira do mecânico ou None se não existir
        """
        try:
            return Carteira.get_by_mecanico(mecanico_id)
            
        except Exception as e:
            logger.error(f"Erro ao obter carteira do mecânico {mecanico_id}: {e}")
            raise
    
    def get_todas_carteiras(self):
        """
        Obtém todas as carteiras (loja e mecânicos).
        
        Returns:
            list: Lista de dicionários com dados das carteiras
        """
        try:
            # Carteira da loja
            carteiras = []
            carteira_loja = self.get_carteira_loja()
            if carteira_loja:
                carteira_loja = dict(carteira_loja)
                carteira_loja['nome'] = 'Loja'
                carteiras.append(carteira_loja)
            
            # Carteiras dos mecânicos
            mecanicos = Mecanico.get_all()
            for mecanico in mecanicos:
                carteira = Carteira.get_by_mecanico(mecanico['id'])
                if carteira:
                    carteira = dict(carteira)
                    carteira['nome'] = mecanico['nome']
                    carteiras.append(carteira)
            
            return carteiras
            
        except Exception as e:
            logger.error(f"Erro ao obter todas as carteiras: {e}")
            raise
    
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
            carteira = Carteira.get_by_id(carteira_id)
            
            if not carteira:
                logger.warning(f"Carteira {carteira_id} não encontrada")
                return []
            
            carteira_obj = Carteira(**dict(carteira))
            movimentacoes = carteira_obj.get_extrato(data_inicio, data_fim)
            
            # Formatação adicional para o extrato
            extrato_formatado = []
            for mov in movimentacoes:
                mov_dict = dict(mov)
                mov_dict['data_formatada'] = format_date(mov['data'])
                mov_dict['valor_formatado'] = format_currency(mov['valor'])
                extrato_formatado.append(mov_dict)
            
            return extrato_formatado
            
        except Exception as e:
            logger.error(f"Erro ao obter extrato da carteira {carteira_id}: {e}")
            raise
    
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
                logger.warning("Tentativa de registrar movimentação com valor zero")
                return False
            
            if valor < 0 and not justificativa:
                logger.error("Tentativa de registrar saída sem justificativa")
                raise ValueError("Justificativa é obrigatória para saídas de valor")
            
            # Obtém a carteira
            carteira = Carteira.get_by_id(carteira_id)
            
            if not carteira:
                logger.error(f"Carteira {carteira_id} não encontrada")
                raise ValueError(f"Carteira ID={carteira_id} não encontrada")
            
            # Cria objeto da carteira
            carteira_obj = Carteira(**dict(carteira))
            
            # Registra a movimentação
            carteira_obj.adicionar_movimentacao(valor, justificativa, servico_id)
            
            logger.info(f"Movimentação registrada: Carteira={carteira_id}, Valor={valor}, Justificativa={justificativa}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar movimentação: {e}")
            raise
    
    def get_resumo_carteiras(self):
        """
        Obtém um resumo dos saldos de todas as carteiras.
        
        Returns:
            dict: Dicionário com resumo dos saldos
        """
        try:
            # Todas as carteiras
            carteiras = self.get_todas_carteiras()
            
            # Agrupamento e totais
            resumo = {
                'carteiras': carteiras,
                'total_loja': 0.0,
                'total_mecanicos': 0.0,
                'total_geral': 0.0
            }
            
            for carteira in carteiras:
                if carteira['tipo'] == 'loja':
                    resumo['total_loja'] += carteira['saldo']
                else:
                    resumo['total_mecanicos'] += carteira['saldo']
                    
                resumo['total_geral'] += carteira['saldo']
            
            return resumo
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo das carteiras: {e}")
            raise
