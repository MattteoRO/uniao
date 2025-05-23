import hashlib
import secrets
import os
from datetime import datetime

from app import db

class Mecanico(db.Model):
    __tablename__ = 'mecanicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    carteira = db.relationship('Carteira', backref='mecanico', uselist=False, 
                              cascade="all, delete-orphan")
    servicos = db.relationship('Servico', backref='mecanico', lazy=True)
    
    def __repr__(self):
        return f'<Mecanico {self.nome}>'

class Carteira(db.Model):
    __tablename__ = 'carteiras'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # 'mecanico' ou 'loja'
    mecanico_id = db.Column(db.Integer, db.ForeignKey('mecanicos.id'))
    saldo = db.Column(db.Float, default=0.0)
    
    # Relacionamentos
    movimentacoes = db.relationship('Movimentacao', backref='carteira', lazy=True, 
                                   cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Carteira {self.id} - {self.tipo}>'

class Movimentacao(db.Model):
    __tablename__ = 'movimentacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    carteira_id = db.Column(db.Integer, db.ForeignKey('carteiras.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    justificativa = db.Column(db.Text)
    data = db.Column(db.DateTime, default=datetime.now)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'))
    
    def __repr__(self):
        return f'<Movimentacao {self.id} - R${self.valor}>'

class ServicoPeca(db.Model):
    __tablename__ = 'servico_pecas'
    
    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    peca_id = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    codigo_barras = db.Column(db.String(50))
    preco_unitario = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<ServicoPeca {self.id} - {self.descricao}>'
    
    @property
    def valor_total(self):
        return self.preco_unitario * self.quantidade

class Servico(db.Model):
    __tablename__ = 'servicos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    mecanico_id = db.Column(db.Integer, db.ForeignKey('mecanicos.id'), nullable=False)
    valor_servico = db.Column(db.Float, nullable=False)
    porcentagem_mecanico = db.Column(db.Integer, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='aberto')  # aberto, concluido, cancelado
    
    # Relacionamentos
    pecas = db.relationship('ServicoPeca', backref='servico', lazy=True, 
                           cascade="all, delete-orphan")
    movimentacoes = db.relationship('Movimentacao', backref='servico', lazy=True)
    
    def __repr__(self):
        return f'<Servico {self.id} - {self.cliente}>'
    
    @property
    def valor_total_pecas(self):
        return sum(peca.valor_total for peca in self.pecas)
    
    @property
    def valor_total(self):
        return self.valor_servico + self.valor_total_pecas
    
    @property
    def valor_mecanico(self):
        # O mecânico recebe a porcentagem APENAS sobre o valor do serviço (mão de obra)
        # Sempre fixado em 80% da mão de obra
        return self.valor_servico * 0.8
    
    @property
    def valor_loja(self):
        # A loja recebe 20% do valor do serviço (mão de obra) + 100% do valor das peças
        return (self.valor_servico * 0.2) + self.valor_total_pecas

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_empresa = db.Column(db.String(100), default='Monark Motopeças e Bicicletaria')
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    caminho_csv = db.Column(db.String(255), default='bdmonarkbd.csv')
    
    def __repr__(self):
        return f'<Configuracao {self.nome_empresa}>'
        
        
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    ativo = db.Column(db.Boolean, default=True)
    admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Usuario {self.username}>'
    
    @staticmethod
    def _gerar_salt():
        """Gera um salt aleatório para a senha"""
        return secrets.token_hex(32)
    
    @staticmethod
    def _hash_senha(senha, salt):
        """Gera o hash da senha usando o salt"""
        senha_com_salt = senha + salt
        # Algoritmo SHA-256
        return hashlib.sha256(senha_com_salt.encode()).hexdigest()
    
    @classmethod
    def criar(cls, username, nome, senha, admin=False):
        """Cria um novo usuário com a senha já hasheada"""
        salt = cls._gerar_salt()
        senha_hash = cls._hash_senha(senha, salt)
        
        usuario = cls(
            username=username,
            nome=nome,
            senha_hash=senha_hash,
            salt=salt,
            admin=admin
        )
        db.session.add(usuario)
        db.session.commit()
        return usuario
    
    def verificar_senha(self, senha):
        """Verifica se a senha está correta"""
        hash_verificacao = self._hash_senha(senha, self.salt)
        return hash_verificacao == self.senha_hash
    
    def alterar_senha(self, nova_senha):
        """Altera a senha do usuário"""
        salt = self._gerar_salt()
        senha_hash = self._hash_senha(nova_senha, salt)
        
        self.senha_hash = senha_hash
        self.salt = salt
        db.session.commit()
        return True


class LogSistema(db.Model):
    __tablename__ = 'logs_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    acao = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    data = db.Column(db.DateTime, default=datetime.now)
    ip = db.Column(db.String(50))
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='logs', lazy=True)
    
    def __repr__(self):
        return f'<LogSistema {self.id} - {self.acao}>'
        
    @classmethod
    def registrar(cls, usuario_id, acao, descricao=None, ip=None):
        """Registra um log no sistema"""
        log = cls(
            usuario_id=usuario_id,
            acao=acao,
            descricao=descricao,
            ip=ip
        )
        db.session.add(log)
        db.session.commit()
        return log