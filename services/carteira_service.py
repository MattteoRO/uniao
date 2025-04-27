"""
Serviço de Gerenciamento de Carteiras
Responsável por criar e gerenciar carteiras e movimentações financeiras.
"""
from flask import current_app
from datetime import datetime

class CarteiraService:
    """Classe de serviço para gerenciamento de carteiras financeiras."""
    
    @staticmethod
    def registrar_movimentacoes_servico(servico):
        """
        Registra as movimentações financeiras de um serviço concluído.
        
        Args:
            servico (Servico): Objeto do serviço concluído
            
        Returns:
            bool: True se as movimentações foram registradas com sucesso
        """
        from app import db
        from models_flask import Carteira, Movimentacao, ServicoPeca
        
        try:
            # Obter peças do serviço
            pecas = ServicoPeca.query.filter_by(servico_id=servico.id).all()
            
            # Calcular valores
            valor_total_pecas = sum(p.preco_unitario * p.quantidade for p in pecas)
            valor_servico = servico.valor_servico
            porcentagem_mecanico = servico.porcentagem_mecanico
            
            # Valor para o mecânico (apenas % da mão de obra)
            valor_mecanico = (valor_servico * porcentagem_mecanico) / 100
            
            # Valor total para a loja (peças + restante da mão de obra)
            valor_loja = valor_total_pecas + (valor_servico - valor_mecanico)
            
            # Verificar se existem as carteiras
            # 1. Carteira da loja
            carteira_loja = Carteira.query.filter_by(tipo='loja').first()
            if not carteira_loja:
                carteira_loja = Carteira(tipo='loja', saldo=0.0)
                db.session.add(carteira_loja)
                db.session.commit()
            
            # 2. Carteira do mecânico
            carteira_mecanico = Carteira.query.filter_by(
                tipo='mecanico', 
                mecanico_id=servico.mecanico_id
            ).first()
            
            if not carteira_mecanico:
                carteira_mecanico = Carteira(
                    tipo='mecanico',
                    mecanico_id=servico.mecanico_id,
                    saldo=0.0
                )
                db.session.add(carteira_mecanico)
                db.session.commit()
            
            # Registrar movimentação para o mecânico
            if valor_mecanico > 0:
                movimentacao_mecanico = Movimentacao(
                    carteira_id=carteira_mecanico.id,
                    valor=valor_mecanico,
                    justificativa=f"Pagamento de serviço #{servico.id}",
                    data=datetime.now(),
                    servico_id=servico.id
                )
                db.session.add(movimentacao_mecanico)
                
                # Atualizar saldo do mecânico
                carteira_mecanico.saldo += valor_mecanico
            
            # Registrar movimentação para a loja
            if valor_loja > 0:
                movimentacao_loja = Movimentacao(
                    carteira_id=carteira_loja.id,
                    valor=valor_loja,
                    justificativa=f"Recebimento de serviço #{servico.id} (peças + % serviço)",
                    data=datetime.now(),
                    servico_id=servico.id
                )
                db.session.add(movimentacao_loja)
                
                # Atualizar saldo da loja
                carteira_loja.saldo += valor_loja
            
            # Salvar todas as alterações
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erro ao registrar movimentações: {str(e)}")
            db.session.rollback()
            return False