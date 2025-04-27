import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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
    
    # Obter filtros da query string
    status_filter = request.args.get('status', 'todos')
    
    # Aplicar filtros
    query = Servico.query
    
    if status_filter != 'todos':
        query = query.filter_by(status=status_filter)
    
    # Ordenar por data de criação (mais recentes primeiro)
    servicos = query.order_by(Servico.data_criacao.desc()).all()
    
    # Obter mecânicos ativos para filtros
    mecanicos = Mecanico.query.filter_by(ativo=True).all()
    
    return render_template('servicos.html', 
                         servicos=servicos, 
                         mecanicos=mecanicos,
                         status_atual=status_filter,
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


@app.route('/servicos/concluir/<int:servico_id>', methods=['POST'])
def concluir_servico(servico_id):
    from models_flask import Servico
    from services.carteira_service import CarteiraService
    
    servico = Servico.query.get_or_404(servico_id)
    
    if servico.status != 'aberto':
        flash(f'Este serviço não pode ser concluído pois não está aberto.', 'danger')
        return redirect(url_for('servicos'))
    
    # Atualizar status
    servico.status = 'concluido'
    db.session.commit()
    
    # Registrar movimentações
    if CarteiraService.registrar_movimentacoes_servico(servico):
        flash(f'Serviço concluído com sucesso e movimentações financeiras registradas!', 'success')
    else:
        flash(f'Serviço concluído, mas houve um erro ao registrar movimentações financeiras.', 'warning')
    
    return redirect(url_for('servicos'))

@app.route('/servicos/cancelar/<int:servico_id>', methods=['POST'])
def cancelar_servico(servico_id):
    from models_flask import Servico
    
    servico = Servico.query.get_or_404(servico_id)
    
    if servico.status != 'aberto':
        flash(f'Este serviço não pode ser cancelado pois não está aberto.', 'danger')
        return redirect(url_for('servicos'))
    
    # Atualizar status
    servico.status = 'cancelado'
    db.session.commit()
    
    flash(f'Serviço cancelado com sucesso!', 'success')
    return redirect(url_for('servicos'))

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
            filename = "preview_cliente.pdf"
        elif tipo == 'mecanico':
            filepath = pdf_generator.gerar_pdf_mecanico(servico_dict, config_dict)
            filename = "preview_mecanico.pdf"
        elif tipo == 'loja':
            filepath = pdf_generator.gerar_pdf_loja(servico_dict, config_dict)
            filename = "preview_loja.pdf"
        else:
            return jsonify({'error': 'Tipo de relatório inválido'})
        
        return jsonify({'success': True, 'filepath': filepath, 'filename': filename})
    
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
        filename = f"servico_{servico_dict['id']}_cliente.pdf"
    elif tipo == 'mecanico':
        filepath = pdf_generator.gerar_pdf_mecanico(servico_dict, config_dict)
        filename = f"servico_{servico_dict['id']}_mecanico.pdf"
    elif tipo == 'loja':
        filepath = pdf_generator.gerar_pdf_loja(servico_dict, config_dict)
        filename = f"servico_{servico_dict['id']}_loja.pdf"
    else:
        return jsonify({'error': 'Tipo de relatório inválido'})
    
    return jsonify({'success': True, 'filepath': filepath, 'filename': filename})

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

# API endpoints
@app.route('/api/carteira/<int:mecanico_id>/movimentacoes', methods=['GET'])
def api_movimentacoes_carteira(mecanico_id):
    """API para obter movimentações da carteira do mecânico."""
    from models_flask import Carteira, Movimentacao
    
    # Verificar se o mecânico existe
    carteira = Carteira.query.filter_by(mecanico_id=mecanico_id).first()
    if not carteira:
        return jsonify({'error': 'Carteira não encontrada'}), 404
    
    # Obter movimentações
    movimentacoes = Movimentacao.query.filter_by(carteira_id=carteira.id).order_by(Movimentacao.data.desc()).all()
    
    # Formatar dados
    resultado = []
    for mov in movimentacoes:
        resultado.append({
            'id': mov.id,
            'valor': mov.valor,
            'justificativa': mov.justificativa,
            'data': mov.data.isoformat(),
            'servico_id': mov.servico_id
        })
    
    return jsonify(resultado)

@app.route('/api/carteira/<int:mecanico_id>/extrato', methods=['GET'])
def api_extrato_carteira(mecanico_id):
    """API para gerar extrato em PDF da carteira do mecânico."""
    from models_flask import Mecanico, Carteira, Movimentacao, Configuracao
    from services.pdf_extrato import PDFExtratoGenerator
    from datetime import datetime, timedelta
    from flask import send_file
    import os
    
    # Verificar se o mecânico existe
    mecanico = Mecanico.query.get_or_404(mecanico_id)
    
    # Verificar se existe a carteira
    carteira = Carteira.query.filter_by(mecanico_id=mecanico_id).first()
    if not carteira:
        return jsonify({'error': 'Carteira não encontrada'}), 404
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Verificar se é para download direto ou retorno JSON
    download_direto = request.args.get('download', 'false').lower() == 'true'
    
    # Converter datas
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            # Último mês
            data_inicio = datetime.now() - timedelta(days=30)
            
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            # Adicionar 1 dia para incluir o dia final
            data_fim = data_fim + timedelta(days=1)
        else:
            data_fim = datetime.now() + timedelta(days=1)
    except ValueError:
        data_inicio = datetime.now() - timedelta(days=30)
        data_fim = datetime.now() + timedelta(days=1)
    
    # Obter movimentações da carteira
    movimentacoes = Movimentacao.query.filter(
        Movimentacao.carteira_id == carteira.id,
        Movimentacao.data >= data_inicio,
        Movimentacao.data <= data_fim
    ).order_by(Movimentacao.data.desc()).all()
    
    # Formatar dados para o PDF
    mecanico_dict = {
        'id': mecanico.id,
        'nome': mecanico.nome,
        'telefone': mecanico.telefone
    }
    
    carteira_dict = {
        'id': carteira.id,
        'saldo': carteira.saldo
    }
    
    movimentacoes_list = []
    for mov in movimentacoes:
        movimentacoes_list.append({
            'id': mov.id,
            'valor': mov.valor,
            'justificativa': mov.justificativa,
            'data': mov.data.strftime('%Y-%m-%dT%H:%M:%S'),
            'servico_id': mov.servico_id
        })
    
    # Obter configurações
    config = Configuracao.query.first()
    if config:
        config_dict = {
            'nome_empresa': config.nome_empresa,
            'endereco': config.endereco,
            'telefone': config.telefone,
            'caminho_csv': config.caminho_csv
        }
    else:
        config_dict = None
    
    # Gerar PDF
    pdf_generator = PDFExtratoGenerator()
    filepath = pdf_generator.gerar_pdf_extrato_mecanico(mecanico_dict, carteira_dict, movimentacoes_list, config_dict)
    
    # Nome do arquivo para download
    filename = f"extrato_mecanico_{mecanico.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Se for download direto, retornar o arquivo
    if download_direto:
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    
    # Caso contrário, retornar JSON com URL do arquivo
    return jsonify({
        'success': True,
        'message': 'Extrato gerado com sucesso',
        'filepath': filepath,
        'filename': filename
    })

@app.route('/api/carteira/<int:mecanico_id>/pagar', methods=['POST'])
def api_pagar_carteira(mecanico_id):
    """API para registrar pagamento e zerar saldo da carteira."""
    from models_flask import Carteira, Movimentacao
    
    # Verificar se o mecânico existe
    carteira = Carteira.query.filter_by(mecanico_id=mecanico_id).first()
    if not carteira:
        return jsonify({'error': 'Carteira não encontrada'}), 404
    
    # Obter dados da requisição
    dados = request.json
    if not dados or 'valor' not in dados:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    valor = float(dados.get('valor', 0))
    justificativa = dados.get('justificativa', 'Pagamento realizado')
    
    # Verificar se o valor é válido (deve ser negativo para pagamento)
    if valor >= 0:
        return jsonify({'error': 'Valor deve ser negativo para pagamento'}), 400
    
    # Registrar a movimentação
    movimentacao = Movimentacao(
        carteira_id=carteira.id,
        valor=valor,
        justificativa=justificativa,
        data=datetime.now()
    )
    
    # Atualizar saldo
    carteira.saldo += valor  # Deve zerar o saldo
    
    # Salvar no banco de dados
    db.session.add(movimentacao)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'saldo_atual': carteira.saldo
    })

@app.route('/relatorios/mecanicos', methods=['GET'])
def relatorio_mecanicos():
    """Página de relatório de lucro por mecânico."""
    from models_flask import Mecanico, Servico, ServicoPeca
    from datetime import datetime, timedelta
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    mecanico_id = request.args.get('mecanico_id')
    
    # Converter datas
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            # Último mês
            data_inicio = datetime.now() - timedelta(days=30)
            
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            # Adicionar 1 dia para incluir o dia final
            data_fim = data_fim + timedelta(days=1)
        else:
            data_fim = datetime.now() + timedelta(days=1)
    except ValueError:
        flash('Data inválida. Usando últimos 30 dias.', 'warning')
        data_inicio = datetime.now() - timedelta(days=30)
        data_fim = datetime.now() + timedelta(days=1)
    
    # Consulta de serviços por mecânico
    servicosQuery = db.session.query(
        Servico
    ).filter(
        Servico.status == 'concluido',
        Servico.data_criacao >= data_inicio,
        Servico.data_criacao <= data_fim
    )
    
    # Filtrar por mecânico específico se necessário
    if mecanico_id:
        servicosQuery = servicosQuery.filter(Servico.mecanico_id == mecanico_id)
    
    servicos = servicosQuery.all()
    
    # Obter todos os mecânicos para o filtro
    mecanicos = Mecanico.query.filter_by(ativo=True).all()
    
    # Dicionário para armazenar dados por mecânico
    mecanicos_dados = {}
    
    # Processar cada serviço
    for servico in servicos:
        mecanico_id = servico.mecanico_id
        
        if mecanico_id not in mecanicos_dados:
            mecanico = Mecanico.query.get(mecanico_id)
            if not mecanico:
                continue
                
            mecanicos_dados[mecanico_id] = {
                'mecanico_id': mecanico.id,
                'mecanico_nome': mecanico.nome,
                'total_servicos': 0,
                'total_pecas': 0,
                'valor_mecanico': 0,
                'valor_loja_servico': 0,
                'valor_loja_pecas': 0,
                'valor_loja_total': 0,
                'valor_total_geral': 0
            }
        
        # Valor do serviço (mão de obra)
        valor_servico = servico.valor_servico or 0
        porcentagem_mecanico = servico.porcentagem_mecanico or 80
        
        # Calcular valor para o mecânico
        valor_mecanico = (valor_servico * porcentagem_mecanico) / 100
        valor_loja_servico = valor_servico - valor_mecanico
        
        # Calcular valor das peças
        total_pecas = 0
        for peca in servico.pecas:
            total_pecas += (peca.preco_unitario * peca.quantidade)
        
        # Atualizar dados do mecânico
        mecanicos_dados[mecanico_id]['total_servicos'] += valor_servico
        mecanicos_dados[mecanico_id]['total_pecas'] += total_pecas
        mecanicos_dados[mecanico_id]['valor_mecanico'] += valor_mecanico
        mecanicos_dados[mecanico_id]['valor_loja_servico'] += valor_loja_servico
        mecanicos_dados[mecanico_id]['valor_loja_pecas'] += total_pecas
        mecanicos_dados[mecanico_id]['valor_loja_total'] += (valor_loja_servico + total_pecas)
        mecanicos_dados[mecanico_id]['valor_total_geral'] += (valor_servico + total_pecas)
    
    # Transformar o dicionário em lista
    relatorio = list(mecanicos_dados.values())
    
    return render_template(
        'relatorio_mecanicos.html',
        relatorio=relatorio,
        mecanicos=mecanicos,
        data_inicio=data_inicio.strftime('%Y-%m-%d'),
        data_fim=(data_fim - timedelta(days=1)).strftime('%Y-%m-%d'),
        mecanico_id=mecanico_id
    )

# Carteira da loja
@app.route('/api/carteira/loja/resumo', methods=['GET'])
def api_resumo_carteira_loja():
    """API para obter resumo financeiro detalhado da carteira da loja."""
    from models_flask import Carteira, Movimentacao, Servico, ServicoPeca, Mecanico
    from datetime import datetime, timedelta
    
    # Obter carteira da loja
    carteira = Carteira.query.filter_by(tipo='loja').first()
    if not carteira:
        return jsonify({'error': 'Carteira da loja não encontrada'}), 404
    
    # Filtros
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Converter datas
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            # Último mês
            data_inicio = datetime.now() - timedelta(days=30)
            
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            # Adicionar 1 dia para incluir o dia final
            data_fim = data_fim + timedelta(days=1)
        else:
            data_fim = datetime.now() + timedelta(days=1)
    except ValueError:
        data_inicio = datetime.now() - timedelta(days=30)
        data_fim = datetime.now() + timedelta(days=1)
    
    # Obter movimentações para o período
    movimentacoes = Movimentacao.query.filter(
        Movimentacao.carteira_id == carteira.id,
        Movimentacao.data >= data_inicio,
        Movimentacao.data <= data_fim
    ).all()
    
    # Calcular resumo financeiro
    resumo = {
        'saldo_atual': carteira.saldo,
        'servicos_valor': 0.0,
        'pecas_valor': 0.0,
        'outras_entradas': 0.0,
        'pagamentos_mecanicos': 0.0,
        'retiradas': 0.0,
        'outros_gastos': 0.0,
        'total_receitas': 0.0,
        'total_despesas': 0.0,
        'lucro_liquido': 0.0
    }
    
    # Serviços concluídos no período
    servicos = Servico.query.filter(
        Servico.status == 'concluido',
        Servico.data_criacao >= data_inicio,
        Servico.data_criacao <= data_fim
    ).all()
    
    # Obter detalhe dos serviços
    servicos_detalhe = []
    for servico in servicos:
        valor_total = servico.valor_servico or 0
        porcentagem_mecanico = servico.porcentagem_mecanico or 80
        
        # Calcular valor para o mecânico
        valor_mecanico = (valor_total * porcentagem_mecanico) / 100
        valor_loja = valor_total - valor_mecanico
        
        # Calcular valor das peças
        valor_pecas = 0
        for peca in servico.pecas:
            valor_pecas += (peca.preco_unitario * peca.quantidade)
        
        # Adicionar em resumo
        resumo['servicos_valor'] += valor_loja
        resumo['pecas_valor'] += valor_pecas
        
        # Adicionar ao detalhe
        mecanico = Mecanico.query.get(servico.mecanico_id)
        servicos_detalhe.append({
            'id': servico.id,
            'descricao': servico.descricao,
            'cliente': servico.cliente,
            'data': servico.data_criacao.strftime('%Y-%m-%dT%H:%M:%S'),
            'mecanico': mecanico.nome if mecanico else 'Não informado',
            'valor_total': valor_total,
            'valor_mecanico': valor_mecanico,
            'valor_loja': valor_loja
        })
    
    # Obter detalhe das peças
    pecas_detalhe = []
    for servico in servicos:
        for peca in servico.pecas:
            pecas_detalhe.append({
                'id': peca.id,
                'servico_id': servico.id,
                'servico_descricao': servico.descricao,
                'data': servico.data_criacao.strftime('%Y-%m-%dT%H:%M:%S'),
                'descricao': peca.descricao,
                'preco_unitario': peca.preco_unitario,
                'quantidade': peca.quantidade,
                'valor_total': peca.preco_unitario * peca.quantidade
            })
    
    # Analisar movimentações
    retiradas_detalhe = []
    for mov in movimentacoes:
        if mov.valor > 0:
            # Receitas
            if 'Serviço' in (mov.justificativa or ''):
                # Já contabilizado em serviços
                pass
            elif 'peças' in (mov.justificativa or '').lower() or 'peça' in (mov.justificativa or '').lower():
                # Já contabilizado em peças
                pass
            else:
                resumo['outras_entradas'] += mov.valor
        else:
            # Despesas
            valor_abs = abs(mov.valor)
            if 'Pagamento' in (mov.justificativa or ''):
                resumo['pagamentos_mecanicos'] += valor_abs
            elif 'Retirada' in (mov.justificativa or ''):
                resumo['retiradas'] += valor_abs
                retiradas_detalhe.append({
                    'id': mov.id,
                    'data': mov.data.strftime('%Y-%m-%dT%H:%M:%S'),
                    'valor': mov.valor,
                    'descricao': mov.justificativa or 'Retirada'
                })
            else:
                resumo['outros_gastos'] += valor_abs
    
    # Calcular totais
    resumo['total_receitas'] = resumo['servicos_valor'] + resumo['pecas_valor'] + resumo['outras_entradas']
    resumo['total_despesas'] = resumo['pagamentos_mecanicos'] + resumo['retiradas'] + resumo['outros_gastos']
    resumo['lucro_liquido'] = resumo['total_receitas'] - resumo['total_despesas']
    
    return jsonify({
        'success': True,
        'resumo': resumo,
        'servicos': servicos_detalhe,
        'pecas': pecas_detalhe,
        'retiradas': retiradas_detalhe
    })

@app.route('/carteira/loja', methods=['GET'])
def carteira_loja():
    """Página da carteira da loja."""
    from models_flask import Carteira, Movimentacao
    from datetime import datetime, timedelta
    
    # Obter carteira da loja
    carteira = Carteira.query.filter_by(tipo='loja').first()
    if not carteira:
        # Criar carteira da loja se não existir
        carteira = Carteira(tipo='loja', mecanico_id=None, saldo=0.0)
        db.session.add(carteira)
        db.session.commit()
    
    # Filtros
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    tipo_movimento = request.args.get('tipo_movimento')
    
    # Converter datas
    try:
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        else:
            # Último mês
            data_inicio = datetime.now() - timedelta(days=30)
            
        if data_fim:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            # Adicionar 1 dia para incluir o dia final
            data_fim = data_fim + timedelta(days=1)
        else:
            data_fim = datetime.now() + timedelta(days=1)
    except ValueError:
        flash('Data inválida. Usando últimos 30 dias.', 'warning')
        data_inicio = datetime.now() - timedelta(days=30)
        data_fim = datetime.now() + timedelta(days=1)
    
    # Construir query base
    query = Movimentacao.query.filter(
        Movimentacao.carteira_id == carteira.id,
        Movimentacao.data >= data_inicio,
        Movimentacao.data <= data_fim
    )
    
    # Filtrar por tipo de movimento
    if tipo_movimento == 'entrada':
        query = query.filter(Movimentacao.valor > 0)
    elif tipo_movimento == 'saida':
        query = query.filter(Movimentacao.valor < 0)
    
    # Obter movimentações ordenadas por data
    movimentacoes = query.order_by(Movimentacao.data.desc()).all()
    
    # Obter movimentações para o gráfico (últimos 30 dias)
    data_grafico_inicio = datetime.now() - timedelta(days=30)
    movimentacoes_grafico = Movimentacao.query.filter(
        Movimentacao.carteira_id == carteira.id,
        Movimentacao.data >= data_grafico_inicio
    ).order_by(Movimentacao.data).all()
    
    return render_template(
        'carteira_loja.html',
        carteira=carteira,
        movimentacoes=movimentacoes,
        movimentacoes_grafico=movimentacoes_grafico,
        data_inicio=data_inicio.strftime('%Y-%m-%d'),
        data_fim=(data_fim - timedelta(days=1)).strftime('%Y-%m-%d'),
        tipo_movimento=tipo_movimento
    )

@app.route('/carteira/loja/movimentacao', methods=['POST'])
def registrar_movimentacao_loja():
    """Registrar nova movimentação na carteira da loja."""
    from models_flask import Carteira, Movimentacao
    
    # Obter carteira da loja
    carteira = Carteira.query.filter_by(tipo='loja').first()
    if not carteira:
        flash('Carteira da loja não encontrada.', 'danger')
        return redirect(url_for('carteira_loja'))
    
    # Obter dados do formulário
    tipo = request.form.get('tipo')
    valor = float(request.form.get('valor', 0))
    justificativa = request.form.get('justificativa', '')
    categoria = request.form.get('categoria', '')
    
    # Validar valor
    if valor <= 0:
        flash('Valor deve ser maior que zero.', 'danger')
        return redirect(url_for('carteira_loja'))
    
    # Ajustar valor de acordo com o tipo
    valor_final = valor if tipo == 'entrada' else -valor
    
    # Adicionar categoria na justificativa
    if categoria:
        justificativa = f"[{categoria}] {justificativa}"
    
    # Criar movimentação
    movimentacao = Movimentacao(
        carteira_id=carteira.id,
        valor=valor_final,
        justificativa=justificativa,
        data=datetime.now()
    )
    
    # Atualizar saldo
    carteira.saldo += valor_final
    
    # Salvar no banco de dados
    db.session.add(movimentacao)
    db.session.commit()
    
    flash(f"{'Entrada' if tipo == 'entrada' else 'Retirada'} registrada com sucesso!", 'success')
    return redirect(url_for('carteira_loja'))

@app.route('/carteira/loja/zerar', methods=['POST'])
def zerar_carteira_loja():
    """Zerar saldo da carteira da loja (saque total)."""
    from models_flask import Carteira, Movimentacao
    
    # Verificar confirmação
    confirmacao = request.form.get('confirmacao')
    if confirmacao != 'CONFIRMAR':
        flash('Confirmação inválida. Operação cancelada.', 'danger')
        return redirect(url_for('carteira_loja'))
    
    # Obter carteira da loja
    carteira = Carteira.query.filter_by(tipo='loja').first()
    if not carteira:
        flash('Carteira da loja não encontrada.', 'danger')
        return redirect(url_for('carteira_loja'))
    
    # Obter saldo atual
    saldo_atual = carteira.saldo
    if saldo_atual <= 0:
        flash('Saldo já está zerado.', 'warning')
        return redirect(url_for('carteira_loja'))
    
    # Criar movimentação negativa para zerar
    justificativa = request.form.get('justificativa', 'Saque total realizado')
    movimentacao = Movimentacao(
        carteira_id=carteira.id,
        valor=-saldo_atual,
        justificativa=f"[SAQUE TOTAL] {justificativa}",
        data=datetime.now()
    )
    
    # Zerar saldo
    carteira.saldo = 0
    
    # Salvar no banco de dados
    db.session.add(movimentacao)
    db.session.commit()
    
    flash(f"Saque total de R$ {saldo_atual:.2f} realizado com sucesso!", 'success')
    return redirect(url_for('carteira_loja'))

# API para obter dados do serviço (para exportação CSV)
@app.route('/servicos/api/<int:servico_id>', methods=['GET'])
def api_servico(servico_id):
    """API para obter dados de um serviço."""
    from models_flask import Servico, ServicoPeca, Mecanico
    
    # Obter serviço
    servico = Servico.query.get(servico_id)
    if not servico:
        return jsonify({'success': False, 'error': 'Serviço não encontrado'}), 404
    
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
        'data_criacao': servico.data_criacao.isoformat(),
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
    
    return jsonify({'success': True, 'servico': servico_dict})

# Rota para excluir serviço
@app.route('/servicos/excluir/<int:servico_id>', methods=['POST'])
def excluir_servico(servico_id):
    """Excluir um serviço do sistema."""
    from models_flask import Servico, ServicoPeca, Movimentacao, Carteira
    
    # Obter serviço
    servico = Servico.query.get_or_404(servico_id)
    
    try:
        # Se o serviço estiver concluído, precisamos ajustar as carteiras
        if servico.status == 'concluido':
            # Obter carteira do mecânico
            carteira_mecanico = Carteira.query.filter_by(mecanico_id=servico.mecanico_id).first()
            
            # Obter carteira da loja
            carteira_loja = Carteira.query.filter_by(tipo='loja').first()
            
            # Se tiver carteiras afetadas (concluído), precisamos reverter saldos
            if carteira_mecanico or carteira_loja:
                # Valor do serviço
                valor_servico = servico.valor_servico
                porcentagem_mecanico = servico.porcentagem_mecanico
                
                # Calcular valores
                valor_mecanico = (valor_servico * porcentagem_mecanico) / 100
                valor_loja_servico = valor_servico - valor_mecanico
                
                # Calcular valor total das peças
                total_pecas = 0
                for peca in servico.pecas:
                    total_pecas += (peca.preco_unitario * peca.quantidade)
                
                # Reverter saldo do mecânico
                if carteira_mecanico and valor_mecanico > 0:
                    carteira_mecanico.saldo -= valor_mecanico
                    # Registrar movimentação negativa
                    movimentacao_mecanico = Movimentacao(
                        carteira_id=carteira_mecanico.id,
                        valor=-valor_mecanico,
                        justificativa=f"Exclusão do serviço #{servico.id} - {servico.cliente}",
                        data=datetime.now()
                    )
                    db.session.add(movimentacao_mecanico)
                
                # Reverter saldo da loja
                if carteira_loja and (valor_loja_servico > 0 or total_pecas > 0):
                    valor_loja_total = valor_loja_servico + total_pecas
                    carteira_loja.saldo -= valor_loja_total
                    # Registrar movimentação negativa
                    movimentacao_loja = Movimentacao(
                        carteira_id=carteira_loja.id,
                        valor=-valor_loja_total,
                        justificativa=f"Exclusão do serviço #{servico.id} - {servico.cliente}",
                        data=datetime.now()
                    )
                    db.session.add(movimentacao_loja)
        
        # Agora exclui todas as movimentações relacionadas ao serviço
        Movimentacao.query.filter_by(servico_id=servico_id).delete()
        
        # Excluir peças relacionadas ao serviço
        ServicoPeca.query.filter_by(servico_id=servico_id).delete()
        
        # Excluir o serviço
        db.session.delete(servico)
        db.session.commit()
        
        flash('Serviço excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir serviço: {str(e)}', 'danger')
    
    return redirect(url_for('servicos'))

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