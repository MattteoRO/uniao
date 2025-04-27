#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from app import app
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monark_system.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Função principal que inicia a aplicação."""
    try:
        # Cria diretórios necessários para relatórios
        dirs = ["ser cliente", "ser mecanico", "ser loja"]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                logger.info(f"Diretório criado: {d}")
        
        # Inicia a aplicação Flask
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}", exc_info=True)

if __name__ == "__main__":
    main()