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
        return self.valor_servico * (self.porcentagem_mecanico / 100)
    
    @property
    def valor_loja(self):
        return self.valor_total - self.valor_mecanico

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_empresa = db.Column(db.String(100), default='Monark Motopeças e Bicicletaria')
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    caminho_csv = db.Column(db.String(255), default='bdmonarkbd.csv')
    
    def __repr__(self):
        return f'<Configuracao {self.nome_empresa}>'