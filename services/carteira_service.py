"""
Serviço para gerenciar carteiras e movimentações financeiras.
"""
from datetime import datetime
from models_flask import db, Carteira, Movimentacao


class CarteiraService:
    """
    Classe para gerenciar as carteiras e movimentações financeiras.
    """
    
    @staticmethod
    def obter_carteira_por_tipo(tipo, mecanico_id=None):
        """
        Obtém uma carteira pelo tipo.
        
        Args:
            tipo (str): Tipo da carteira ('mecanico' ou 'loja')
            mecanico_id (int, optional): ID do mecânico (para tipo 'mecanico')
            
        Returns:
            Carteira: Instância da carteira ou None se não encontrada
        """
        if tipo == 'mecanico' and mecanico_id:
            return Carteira.query.filter_by(tipo=tipo, mecanico_id=mecanico_id).first()
        elif tipo == 'loja':
            return Carteira.query.filter_by(tipo=tipo).first()
        return None
    
    @staticmethod
    def obter_carteira_loja():
        """
        Obtém a carteira da loja.
        
        Returns:
            Carteira: Instância da carteira da loja ou None se não encontrada
        """
        return Carteira.query.filter_by(tipo='loja').first()
    
    @staticmethod
    def obter_carteira_mecanico(mecanico_id):
        """
        Obtém a carteira de um mecânico.
        
        Args:
            mecanico_id (int): ID do mecânico
            
        Returns:
            Carteira: Instância da carteira do mecânico ou None se não encontrada
        """
        return Carteira.query.filter_by(tipo='mecanico', mecanico_id=mecanico_id).first()
    
    @staticmethod
    def registrar_movimentacao(carteira_id, valor, justificativa, servico_id=None):
        """
        Registra uma movimentação em uma carteira.
        
        Args:
            carteira_id (int): ID da carteira
            valor (float): Valor da movimentação (positivo para entrada, negativo para saída)
            justificativa (str): Justificativa da movimentação
            servico_id (int, optional): ID do serviço relacionado
            
        Returns:
            bool: True se a movimentação foi registrada com sucesso
        """
        try:
            # Obter a carteira
            carteira = Carteira.query.get(carteira_id)
            if not carteira:
                return False
            
            # Criar a movimentação
            movimentacao = Movimentacao(
                carteira_id=carteira_id,
                valor=valor,
                justificativa=justificativa,
                data=datetime.now(),
                servico_id=servico_id
            )
            
            # Atualizar o saldo da carteira
            carteira.saldo += valor
            
            # Salvar no banco de dados
            db.session.add(movimentacao)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Erro ao registrar movimentação: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def registrar_movimentacoes_servico(servico):
        """
        Registra as movimentações financeiras de um serviço.
        
        Args:
            servico: Instância do serviço
            
        Returns:
            bool: True se as movimentações foram registradas com sucesso
        """
        try:
            # Obter carteira do mecânico
            carteira_mecanico = CarteiraService.obter_carteira_mecanico(servico.mecanico_id)
            if not carteira_mecanico:
                return False
            
            # Obter carteira da loja
            carteira_loja = CarteiraService.obter_carteira_loja()
            if not carteira_loja:
                return False
            
            # Calcular valores
            valor_mecanico = (servico.valor_servico * servico.porcentagem_mecanico) / 100
            valor_loja_servico = servico.valor_servico - valor_mecanico
            
            # Calcular valor das peças
            from models_flask import ServicoPeca
            pecas = ServicoPeca.query.filter_by(servico_id=servico.id).all()
            valor_pecas = sum(p.preco_unitario * p.quantidade for p in pecas)
            
            # Registrar movimentação para o mecânico (serviço)
            if valor_mecanico > 0:
                CarteiraService.registrar_movimentacao(
                    carteira_mecanico.id,
                    valor_mecanico,
                    f"Serviço #{servico.id} - {servico.porcentagem_mecanico}% do valor do serviço",
                    servico.id
                )
            
            # Registrar movimentação para a loja (serviço)
            if valor_loja_servico > 0:
                CarteiraService.registrar_movimentacao(
                    carteira_loja.id,
                    valor_loja_servico,
                    f"Serviço #{servico.id} - Valor do serviço (parte da loja)",
                    servico.id
                )
            
            # Registrar movimentação para a loja (peças)
            if valor_pecas > 0:
                CarteiraService.registrar_movimentacao(
                    carteira_loja.id,
                    valor_pecas,
                    f"Serviço #{servico.id} - Valor das peças",
                    servico.id
                )
            
            return True
        except Exception as e:
            print(f"Erro ao registrar movimentações do serviço: {e}")
            db.session.rollback()
            return False