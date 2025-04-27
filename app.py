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
    from datetime import datetime
    now = datetime.now()
    return render_template('index.html', now=now)

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
    except Exception as e:
        print(f"Erro na inicialização do banco de dados: {e}")
        # Se houve erro na criação de tabelas, provavelmente é porque elas já existem

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)