"""
Serviço de Backup e Restauração
Responsável por exportar e importar dados do sistema para backup e restauração.
"""
import os
import json
import datetime
import shutil
from flask import current_app

from app import db
from models_flask import (
    Mecanico, Carteira, Movimentacao, Servico, ServicoPeca, 
    Configuracao, Usuario, LogSistema
)

class BackupService:
    """Classe de serviço para backup e restauração do sistema."""
    
    BACKUP_DIR = "backups"
    LOG_DIR = "logs"
    
    @classmethod
    def ensure_dirs(cls):
        """Garante que os diretórios de backup e logs existam."""
        # Criar diretório de backups se não existir
        if not os.path.exists(cls.BACKUP_DIR):
            os.makedirs(cls.BACKUP_DIR)
        
        # Criar diretório de logs se não existir
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)
    
    @classmethod
    def exportar_dados(cls, usuario_id=None):
        """
        Exporta todos os dados do sistema para um arquivo JSON.
        
        Args:
            usuario_id (int, optional): ID do usuário que solicitou o backup
            
        Returns:
            str: Caminho do arquivo gerado
        """
        cls.ensure_dirs()
        
        # Coletar dados de todas as tabelas
        dados = {
            'data_backup': datetime.datetime.now().isoformat(),
            'mecanicos': [],
            'carteiras': [],
            'movimentacoes': [],
            'servicos': [],
            'servico_pecas': [],
            'configuracoes': [],
            'usuarios': []
        }
        
        # Adicionar dados de mecânicos
        for mecanico in Mecanico.query.all():
            dados['mecanicos'].append({
                'id': mecanico.id,
                'nome': mecanico.nome,
                'telefone': mecanico.telefone,
                'data_cadastro': mecanico.data_cadastro.isoformat(),
                'ativo': mecanico.ativo
            })
        
        # Adicionar dados de carteiras
        for carteira in Carteira.query.all():
            dados['carteiras'].append({
                'id': carteira.id,
                'tipo': carteira.tipo,
                'mecanico_id': carteira.mecanico_id,
                'saldo': carteira.saldo
            })
        
        # Adicionar dados de movimentações
        for mov in Movimentacao.query.all():
            dados['movimentacoes'].append({
                'id': mov.id,
                'carteira_id': mov.carteira_id,
                'valor': mov.valor,
                'justificativa': mov.justificativa,
                'data': mov.data.isoformat(),
                'servico_id': mov.servico_id
            })
        
        # Adicionar dados de serviços
        for servico in Servico.query.all():
            dados['servicos'].append({
                'id': servico.id,
                'cliente': servico.cliente,
                'telefone': servico.telefone,
                'descricao': servico.descricao,
                'mecanico_id': servico.mecanico_id,
                'valor_servico': servico.valor_servico,
                'porcentagem_mecanico': servico.porcentagem_mecanico,
                'data_criacao': servico.data_criacao.isoformat(),
                'status': servico.status
            })
        
        # Adicionar dados de peças de serviços
        for peca in ServicoPeca.query.all():
            dados['servico_pecas'].append({
                'id': peca.id,
                'servico_id': peca.servico_id,
                'peca_id': peca.peca_id,
                'descricao': peca.descricao,
                'codigo_barras': peca.codigo_barras,
                'preco_unitario': peca.preco_unitario,
                'quantidade': peca.quantidade
            })
        
        # Adicionar dados de configurações
        for config in Configuracao.query.all():
            dados['configuracoes'].append({
                'id': config.id,
                'nome_empresa': config.nome_empresa,
                'endereco': config.endereco,
                'telefone': config.telefone,
                'caminho_csv': config.caminho_csv
            })
        
        # Adicionar dados de usuários (sem senha)
        for usuario in Usuario.query.all():
            dados['usuarios'].append({
                'id': usuario.id,
                'username': usuario.username,
                'nome': usuario.nome,
                'data_cadastro': usuario.data_cadastro.isoformat(),
                'ativo': usuario.ativo,
                'admin': usuario.admin
            })
        
        # Gerar nome do arquivo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json"
        filepath = os.path.join(cls.BACKUP_DIR, filename)
        
        # Salvar dados no arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        
        # Registrar log
        if usuario_id:
            LogSistema.registrar(
                usuario_id=usuario_id,
                acao="Backup do Sistema",
                descricao=f"Backup completo gerado: {filename}"
            )
        
        return filepath
    
    @classmethod
    def importar_dados(cls, filepath, usuario_id=None):
        """
        Importa dados do sistema a partir de um arquivo JSON.
        
        Args:
            filepath (str): Caminho do arquivo a ser importado
            usuario_id (int, optional): ID do usuário que solicitou a importação
            
        Returns:
            bool: True se a importação foi bem-sucedida
        """
        # Verificar se o arquivo existe
        if not os.path.exists(filepath):
            return False
        
        # Fazer backup antes de importar
        cls.exportar_dados(usuario_id)
        
        try:
            # Ler dados do arquivo
            with open(filepath, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Limpar todas as tabelas
            db.session.query(ServicoPeca).delete()
            db.session.query(Movimentacao).delete()
            db.session.query(Servico).delete()
            db.session.query(Carteira).delete()
            db.session.query(Mecanico).delete()
            db.session.query(Configuracao).delete()
            db.session.commit()
            
            # Não remover usuários para manter o login atual
            
            # Importar dados de mecânicos
            for mecanico_data in dados.get('mecanicos', []):
                mecanico = Mecanico(
                    id=mecanico_data['id'],
                    nome=mecanico_data['nome'],
                    telefone=mecanico_data.get('telefone'),
                    data_cadastro=datetime.datetime.fromisoformat(mecanico_data['data_cadastro']),
                    ativo=mecanico_data['ativo']
                )
                db.session.add(mecanico)
            
            db.session.commit()
            
            # Importar dados de carteiras
            for carteira_data in dados.get('carteiras', []):
                carteira = Carteira(
                    id=carteira_data['id'],
                    tipo=carteira_data['tipo'],
                    mecanico_id=carteira_data.get('mecanico_id'),
                    saldo=carteira_data['saldo']
                )
                db.session.add(carteira)
            
            db.session.commit()
            
            # Importar dados de serviços
            for servico_data in dados.get('servicos', []):
                servico = Servico(
                    id=servico_data['id'],
                    cliente=servico_data['cliente'],
                    telefone=servico_data['telefone'],
                    descricao=servico_data['descricao'],
                    mecanico_id=servico_data['mecanico_id'],
                    valor_servico=servico_data['valor_servico'],
                    porcentagem_mecanico=servico_data['porcentagem_mecanico'],
                    data_criacao=datetime.datetime.fromisoformat(servico_data['data_criacao']),
                    status=servico_data['status']
                )
                db.session.add(servico)
            
            db.session.commit()
            
            # Importar dados de peças de serviços
            for peca_data in dados.get('servico_pecas', []):
                peca = ServicoPeca(
                    id=peca_data['id'],
                    servico_id=peca_data['servico_id'],
                    peca_id=peca_data['peca_id'],
                    descricao=peca_data['descricao'],
                    codigo_barras=peca_data.get('codigo_barras'),
                    preco_unitario=peca_data['preco_unitario'],
                    quantidade=peca_data['quantidade']
                )
                db.session.add(peca)
            
            db.session.commit()
            
            # Importar dados de movimentações
            for mov_data in dados.get('movimentacoes', []):
                mov = Movimentacao(
                    id=mov_data['id'],
                    carteira_id=mov_data['carteira_id'],
                    valor=mov_data['valor'],
                    justificativa=mov_data.get('justificativa'),
                    data=datetime.datetime.fromisoformat(mov_data['data']),
                    servico_id=mov_data.get('servico_id')
                )
                db.session.add(mov)
            
            db.session.commit()
            
            # Importar dados de configurações
            for config_data in dados.get('configuracoes', []):
                config = Configuracao(
                    id=config_data['id'],
                    nome_empresa=config_data['nome_empresa'],
                    endereco=config_data.get('endereco'),
                    telefone=config_data.get('telefone'),
                    caminho_csv=config_data.get('caminho_csv', 'bdmonarkbd.csv')
                )
                db.session.add(config)
            
            db.session.commit()
            
            # Registrar log
            if usuario_id:
                LogSistema.registrar(
                    usuario_id=usuario_id,
                    acao="Restauração do Sistema",
                    descricao=f"Dados importados do arquivo: {os.path.basename(filepath)}"
                )
            
            return True
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao importar dados: {str(e)}")
            
            # Registrar log de erro
            if usuario_id:
                LogSistema.registrar(
                    usuario_id=usuario_id,
                    acao="Erro na Restauração",
                    descricao=f"Erro ao importar dados: {str(e)}"
                )
            
            return False
    
    @classmethod
    def resetar_sistema(cls, usuario_id=None):
        """
        Restaura o sistema para o estado inicial, limpando todos os dados.
        
        Args:
            usuario_id (int, optional): ID do usuário que solicitou o reset
            
        Returns:
            bool: True se o reset foi bem-sucedido
        """
        # Fazer backup antes de resetar
        cls.exportar_dados(usuario_id)
        
        try:
            # Limpar todas as tabelas
            db.session.query(ServicoPeca).delete()
            db.session.query(Movimentacao).delete()
            db.session.query(Servico).delete()
            db.session.query(Carteira).delete()
            db.session.query(Mecanico).delete()
            
            # Manter apenas o usuário administrador padrão
            for usuario in Usuario.query.filter(Usuario.username != "1").all():
                db.session.delete(usuario)
            
            # Resetar as configurações
            db.session.query(Configuracao).delete()
            config = Configuracao(
                nome_empresa='Monark Motopeças e Bicicletaria',
                endereco='',
                telefone='',
                caminho_csv='bdmonarkbd.csv'
            )
            db.session.add(config)
            
            # Limpar logs (exceto o do reset)
            db.session.query(LogSistema).delete()
            
            db.session.commit()
            
            # Registrar log do reset
            if usuario_id:
                LogSistema.registrar(
                    usuario_id=usuario_id,
                    acao="Reset do Sistema",
                    descricao="Sistema restaurado para o estado inicial"
                )
            
            return True
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao resetar sistema: {str(e)}")
            
            # Registrar log de erro
            if usuario_id:
                LogSistema.registrar(
                    usuario_id=usuario_id,
                    acao="Erro no Reset",
                    descricao=f"Erro ao resetar sistema: {str(e)}"
                )
            
            return False