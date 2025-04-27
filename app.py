import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

import filters


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "monark_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///monark_system.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension
db.init_app(app)

# Registro de filtros Jinja
filters.init_app(app)

# Rotas e visualizações
@app.route('/')
def index():
    from models_flask import Servico, Mecanico, Carteira
    from datetime import datetime
    
    # Obter estatísticas
    servicos_ativos = Servico.query.filter_by(status='aberto').count()
    servicos_concluidos = Servico.query.filter_by(status='concluido').count()
    mecanicos_ativos = Mecanico.query.filter_by(ativo=True).count()
    
    # Obter saldo da loja
    carteira_loja = Carteira.query.filter_by(tipo='loja').first()
    saldo_loja = carteira_loja.saldo if carteira_loja else 0
    
    # Obter serviços recentes
    servicos_recentes = Servico.query.order_by(Servico.data_criacao.desc()).limit(5).all()
    
    # Mapear status para classes de badge
    for servico in servicos_recentes:
        if servico.status == 'aberto':
            servico.status_badge = 'bg-primary'
        elif servico.status == 'concluido':
            servico.status_badge = 'bg-success'
        elif servico.status == 'cancelado':
            servico.status_badge = 'bg-danger'
        else:
            servico.status_badge = 'bg-secondary'
    
    now = datetime.now()
    return render_template('index.html', 
                          now=now,
                          servicos_ativos=servicos_ativos,
                          servicos_concluidos=servicos_concluidos,
                          mecanicos_ativos=mecanicos_ativos, 
                          saldo_loja=saldo_loja,
                          servicos_recentes=servicos_recentes)

@app.route('/mecanicos', methods=['GET', 'POST'])
def mecanicos():
    from models_flask import Mecanico, Carteira
    from datetime import datetime
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        
        if nome:
            # Criar novo mecânico
            mecanico = Mecanico(
                nome=nome,
                telefone=telefone,
                data_cadastro=datetime.now(),
                ativo=True
            )
            db.session.add(mecanico)
            db.session.commit()
            
            # Criar carteira para o mecânico
            carteira = Carteira(
                tipo='mecanico',
                mecanico_id=mecanico.id,
                saldo=0.0
            )
            db.session.add(carteira)
            db.session.commit()
            
            flash(f'Mecânico {nome} cadastrado com sucesso!', 'success')
            return redirect(url_for('mecanicos'))
        else:
            flash('O nome do mecânico é obrigatório!', 'danger')
    
    # Por padrão, mostrar apenas mecânicos ativos
    mostrar_inativos = request.args.get('mostrar_inativos', 'false') == 'true'
    
    if mostrar_inativos:
        mecanicos = Mecanico.query.all()
    else:
        mecanicos = Mecanico.query.filter_by(ativo=True).all()
        
    return render_template('mecanicos.html', mecanicos=mecanicos, now=datetime.now())


@app.route('/mecanicos/ativar/<int:mecanico_id>')
def ativar_mecanico(mecanico_id):
    from models_flask import Mecanico
    
    mecanico = Mecanico.query.get_or_404(mecanico_id)
    if not mecanico.ativo:
        mecanico.ativo = True
        db.session.commit()
        flash(f'Mecânico {mecanico.nome} ativado com sucesso!', 'success')
    
    return redirect(url_for('mecanicos'))


@app.route('/mecanicos/desativar/<int:mecanico_id>')
def desativar_mecanico(mecanico_id):
    from models_flask import Mecanico
    
    mecanico = Mecanico.query.get_or_404(mecanico_id)
    if mecanico.ativo:
        mecanico.ativo = False
        db.session.commit()
        flash(f'Mecânico {mecanico.nome} desativado com sucesso!', 'success')
    
    return redirect(url_for('mecanicos'))

@app.route('/servicos')
def servicos():
    from models_flask import Servico, Mecanico
    from datetime import datetime
    
    servicos = Servico.query.all()
    mecanicos = Mecanico.query.filter_by(ativo=True).all()
    return render_template('servicos.html', 
                          servicos=servicos, 
                          mecanicos=mecanicos,
                          now=datetime.now())


@app.route('/servicos/novo', methods=['GET', 'POST'])
def novo_servico():
    from models_flask import Servico, Mecanico, ServicoPeca, Configuracao
    from services.csv_manager import CSVManager
    from services.pdf_generator import PDFGenerator
    from datetime import datetime
    import json
    
    # Obter mecânicos ativos
    mecanicos = Mecanico.query.filter_by(ativo=True).all()
    
    # Obter configurações
    config = Configuracao.query.first()
    porcentagem_padrao = 80  # 80% é a porcentagem padrão para o mecânico
    
    # Criar gerenciador CSV
    csv_manager = CSVManager(config.caminho_csv if config else 'bdmonarkbd.csv')
    
    if request.method == 'POST':
        # Parsear dados do formulário
        cliente = request.form.get('cliente')
        telefone = request.form.get('telefone')
        descricao = request.form.get('descricao')
        mecanico_id = request.form.get('mecanico_id')
        valor_servico = float(request.form.get('valor_servico', 0))
        porcentagem_mecanico = int(request.form.get('porcentagem_mecanico', porcentagem_padrao))
        pecas_json = request.form.get('pecas_json', '[]')
        
        # Converter string JSON para lista de peças
        pecas = json.loads(pecas_json)
        
        # Criar serviço
        servico = Servico(
            cliente=cliente,
            telefone=telefone,
            descricao=descricao,
            mecanico_id=int(mecanico_id),
            valor_servico=valor_servico,
            porcentagem_mecanico=porcentagem_mecanico,
            data_criacao=datetime.now(),
            status='aberto'
        )
        
        db.session.add(servico)
        db.session.commit()
        
        # Adicionar peças ao serviço
        for peca in pecas:
            servico_peca = ServicoPeca(
                servico_id=servico.id,
                peca_id=peca['id'],
                descricao=peca['descricao'],
                codigo_barras=peca.get('codigo_barras', ''),
                preco_unitario=float(peca['preco']),
                quantidade=int(peca['quantidade'])
            )
            db.session.add(servico_peca)
        
        db.session.commit()
        
        flash(f'Serviço cadastrado com sucesso!', 'success')
        return redirect(url_for('servicos'))
    
    # Para GET, mostrar o formulário
    return render_template('novo_servico.html', 
                          mecanicos=mecanicos, 
                          porcentagem_padrao=porcentagem_padrao,
                          now=datetime.now())


@app.route('/api/pecas/buscar')
def buscar_pecas():
    from services.csv_manager import CSVManager
    from models_flask import Configuracao
    
    termo = request.args.get('termo', '')
    
    # Obter configurações
    config = Configuracao.query.first()
    caminho_csv = config.caminho_csv if config else 'bdmonarkbd.csv'
    
    # Buscar peças no CSV
    csv_manager = CSVManager(caminho_csv)
    pecas = csv_manager.buscar_pecas(termo)
    
    return jsonify(pecas)


@app.route('/servicos/gerar_pdf/<int:servico_id>/<tipo>', methods=['GET', 'POST'])
def gerar_pdf_servico(servico_id, tipo):
    from models_flask import Servico, Mecanico, ServicoPeca, Configuracao
    from services.pdf_generator import PDFGenerator
    
    # Obter configurações
    config = Configuracao.query.first()
    if not config:
        config = Configuracao(
            nome_empresa='Monark Motopeças e Bicicletaria',
            endereco='Endereço não cadastrado',
            telefone='',
            caminho_csv='bdmonarkbd.csv'
        )
        db.session.add(config)
        db.session.commit()
    
    # Preparar configurações
    config_dict = {
        'nome_empresa': config.nome_empresa,
        'endereco': config.endereco,
        'telefone': config.telefone,
        'caminho_csv': config.caminho_csv
    }
    
    # Verificar se estamos recebendo dados via POST (preview antes de salvar)
    if request.method == 'POST' and servico_id == 0:
        # Receber dados do serviço diretamente do corpo da requisição
        servico_dict = request.json
        
        # Gerar PDF
        pdf_generator = PDFGenerator()
        
        if tipo == 'cliente':
            filepath = pdf_generator.gerar_pdf_cliente(servico_dict, config_dict)
        elif tipo == 'mecanico':
            filepath = pdf_generator.gerar_pdf_mecanico(servico_dict, config_dict)
        elif tipo == 'loja':
            filepath = pdf_generator.gerar_pdf_loja(servico_dict, config_dict)
        else:
            return jsonify({'error': 'Tipo de relatório inválido'})
        
        return jsonify({'success': True, 'filepath': filepath})
    
    # Caso normal: obter serviço do banco de dados
    servico = Servico.query.get_or_404(servico_id)
    
    # Obter mecânico
    mecanico = Mecanico.query.get(servico.mecanico_id)
    
    # Obter peças
    pecas = ServicoPeca.query.filter_by(servico_id=servico_id).all()
    
    # Preparar dados do serviço
    servico_dict = {
        'id': servico.id,
        'cliente': servico.cliente,
        'telefone': servico.telefone,
        'descricao': servico.descricao,
        'mecanico_id': servico.mecanico_id,
        'mecanico_nome': mecanico.nome if mecanico else '',
        'valor_servico': servico.valor_servico,
        'porcentagem_mecanico': servico.porcentagem_mecanico,
        'data_criacao': servico.data_criacao,
        'status': servico.status,
        'pecas': [{
            'id': p.id,
            'peca_id': p.peca_id,
            'descricao': p.descricao,
            'codigo_barras': p.codigo_barras,
            'preco_unitario': p.preco_unitario,
            'quantidade': p.quantidade
        } for p in pecas],
        'valor_total_pecas': sum(p.preco_unitario * p.quantidade for p in pecas)
    }
    
    # Gerar PDF
    pdf_generator = PDFGenerator()
    
    if tipo == 'cliente':
        filepath = pdf_generator.gerar_pdf_cliente(servico_dict, config_dict)
    elif tipo == 'mecanico':
        filepath = pdf_generator.gerar_pdf_mecanico(servico_dict, config_dict)
    elif tipo == 'loja':
        filepath = pdf_generator.gerar_pdf_loja(servico_dict, config_dict)
    else:
        return jsonify({'error': 'Tipo de relatório inválido'})
    
    return jsonify({'success': True, 'filepath': filepath})

@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    from models_flask import Configuracao
    from datetime import datetime
    
    if request.method == 'POST':
        nome_empresa = request.form.get('nome_empresa')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')
        caminho_csv = request.form.get('caminho_csv')
        
        config = Configuracao.query.first()
        if not config:
            config = Configuracao(
                nome_empresa=nome_empresa,
                endereco=endereco,
                telefone=telefone,
                caminho_csv=caminho_csv
            )
            db.session.add(config)
        else:
            config.nome_empresa = nome_empresa
            config.endereco = endereco
            config.telefone = telefone
            config.caminho_csv = caminho_csv
            
        db.session.commit()
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('configuracoes'))
    
    config = Configuracao.query.first()
    if not config:
        config = Configuracao(
            nome_empresa='Monark Motopeças e Bicicletaria',
            endereco='Endereço não cadastrado',
            telefone='',
            caminho_csv='bdmonarkbd.csv'
        )
        db.session.add(config)
        db.session.commit()
        
    return render_template('configuracoes.html', config=config, now=datetime.now())

# Inicialização do banco de dados
with app.app_context():
    # Import models here to ensure they're registered with SQLAlchemy
    import models_flask
    
    try:
        # Try to create missing tables only
        db.create_all()
        
        # Ensure a default configuration exists
        config = models_flask.Configuracao.query.first()
        if not config:
            config = models_flask.Configuracao(
                nome_empresa='Monark Motopeças e Bicicletaria',
                endereco='Endereço não cadastrado',
                telefone='',
                caminho_csv='bdmonarkbd.csv'
            )
            db.session.add(config)
            db.session.commit()
        
        # Ensure a wallet for the store exists
        carteira_loja = models_flask.Carteira.query.filter_by(tipo='loja').first()
        if not carteira_loja:
            carteira_loja = models_flask.Carteira(
                tipo='loja',
                mecanico_id=None,
                saldo=0.0
            )
            db.session.add(carteira_loja)
            db.session.commit()
    except Exception as e:
        print(f"Erro na inicialização do banco de dados: {e}")
        # Se houve erro na criação de tabelas, provavelmente é porque elas já existem

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)