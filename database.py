# -*- coding: utf-8 -*-

"""
Módulo de banco de dados
Responsável pela conexão e inicialização do banco de dados SQLite.
"""

import os
import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Caminho do banco de dados
DB_PATH = 'monark_system.db'

@contextmanager
def get_db_connection():
    """
    Gerenciador de contexto para conexão com o banco de dados.
    Garante que a conexão é fechada após o uso.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permite acessar as colunas pelo nome
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(query, params=(), fetch_all=False, fetch_one=False, commit=False):
    """
    Executa uma query no banco de dados.
    
    Args:
        query (str): A query SQL a ser executada
        params (tuple): Parâmetros para a query
        fetch_all (bool): Se deve retornar todos os resultados
        fetch_one (bool): Se deve retornar apenas um resultado
        commit (bool): Se deve fazer commit após a execução
        
    Returns:
        list, dict, int, None: Resultados da query, quantidade de linhas afetadas ou None
    """
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if commit:
                conn.commit()
                return cursor.rowcount
            
            if fetch_all:
                return cursor.fetchall()
            
            if fetch_one:
                return cursor.fetchone()
            
            return None
        except sqlite3.Error as e:
            logger.error(f"Erro ao executar query: {e}\nQuery: {query}\nParâmetros: {params}")
            conn.rollback()
            raise

def init_db():
    """
    Inicializa o banco de dados com as tabelas necessárias se ainda não existirem.
    """
    try:
        # Verifica se o banco de dados já existe
        db_exists = os.path.exists(DB_PATH)
        
        # Criação das tabelas
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de mecânicos
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS mecanicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                data_cadastro TEXT NOT NULL,
                ativo INTEGER DEFAULT 1
            )
            ''')
            
            # Tabela de carteiras digitais
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS carteiras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,  -- 'mecanico' ou 'loja'
                mecanico_id INTEGER,
                saldo REAL DEFAULT 0.0,
                FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
            )
            ''')
            
            # Tabela de movimentações nas carteiras
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carteira_id INTEGER NOT NULL,
                valor REAL NOT NULL,
                justificativa TEXT,
                data TEXT NOT NULL,
                servico_id INTEGER,
                FOREIGN KEY (carteira_id) REFERENCES carteiras(id),
                FOREIGN KEY (servico_id) REFERENCES servicos(id)
            )
            ''')
            
            # Tabela de serviços
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                telefone TEXT NOT NULL,
                descricao TEXT NOT NULL,
                mecanico_id INTEGER NOT NULL,
                valor_servico REAL NOT NULL,
                porcentagem_mecanico REAL NOT NULL,
                data_criacao TEXT NOT NULL,
                status TEXT DEFAULT 'aberto',
                FOREIGN KEY (mecanico_id) REFERENCES mecanicos(id)
            )
            ''')
            
            # Tabela de peças utilizadas nos serviços
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS servico_pecas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servico_id INTEGER NOT NULL,
                peca_id TEXT NOT NULL,
                descricao TEXT NOT NULL,
                codigo_barras TEXT,
                preco_unitario REAL NOT NULL,
                quantidade INTEGER NOT NULL,
                FOREIGN KEY (servico_id) REFERENCES servicos(id)
            )
            ''')
            
            # Tabela de configurações
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_empresa TEXT DEFAULT 'Monark Motopeças e Bicicletaria',
                endereco TEXT,
                telefone TEXT,
                caminho_csv TEXT DEFAULT 'bdmonarkbd.csv'
            )
            ''')
            
            # Inserção de configurações iniciais se o banco de dados foi criado agora
            if not db_exists:
                # Cria carteira padrão da loja
                cursor.execute('''
                INSERT INTO carteiras (tipo, mecanico_id, saldo)
                VALUES ('loja', NULL, 0.0)
                ''')
                
                # Insere configurações padrão
                cursor.execute('''
                INSERT INTO configuracoes (nome_empresa, endereco, telefone, caminho_csv)
                VALUES ('Monark Motopeças e Bicicletaria', 'Endereço não cadastrado', '', 'bdmonarkbd.csv')
                ''')
            
            conn.commit()
            
            logger.info("Banco de dados inicializado com sucesso")
            
    except sqlite3.Error as e:
        logger.error(f"Erro ao inicializar o banco de dados: {e}")
        raise
