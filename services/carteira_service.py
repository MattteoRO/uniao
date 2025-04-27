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
            
            # Valor para o mecânico (sempre 80% da mão de obra)
            valor_mecanico = (valor_servico * 80) / 100
            
            # Valor da mão de obra para a loja (20% da mão de obra)
            valor_loja_servico = (valor_servico * 20) / 100
            
            # Valor total para a loja (100% das peças + 20% da mão de obra)
            valor_loja = valor_total_pecas + valor_loja_servico
            
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
            
            # Registrar movimentação para a loja (parte da mão de obra)
            if valor_loja_servico > 0:
                movimentacao_loja_servico = Movimentacao(
                    carteira_id=carteira_loja.id,
                    valor=valor_loja_servico,
                    justificativa=f"Recebimento de serviço #{servico.id} (20% da mão de obra)",
                    data=datetime.now(),
                    servico_id=servico.id
                )
                db.session.add(movimentacao_loja_servico)
                
                # Atualizar saldo da loja
                carteira_loja.saldo += valor_loja_servico
            
            # Registrar movimentação para a loja (peças)
            if valor_total_pecas > 0:
                movimentacao_loja_pecas = Movimentacao(
                    carteira_id=carteira_loja.id,
                    valor=valor_total_pecas,
                    justificativa=f"Peças do serviço #{servico.id}",
                    data=datetime.now(),
                    servico_id=servico.id
                )
                db.session.add(movimentacao_loja_pecas)
                
                # Atualizar saldo da loja
                carteira_loja.saldo += valor_total_pecas
            
            # Salvar todas as alterações
            db.session.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erro ao registrar movimentações: {str(e)}")
            db.session.rollback()
            return False