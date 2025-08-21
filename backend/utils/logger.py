"""
Sistema de Logging Profissional
Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614

Este módulo configura o sistema de logging da aplicação com
múltiplos handlers, formatação e rotação de arquivos.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from config.settings import Config


class ColoredFormatter(logging.Formatter):
    """Formatter colorido para console."""
    
    # Códigos de cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarelo
        'ERROR': '\033[31m',      # Vermelho
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Adicionar cor ao levelname
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Configura e retorna um logger profissional.
    
    Args:
        name: Nome do logger (geralmente __name__)
        level: Nível de log (opcional)
        
    Returns:
        Logger configurado
    """
    # Obter nível de log
    log_level = level or Config.LOG_LEVEL
    
    # Criar logger
    logger = logging.getLogger(name)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formato para arquivo
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formato para console
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Handler para arquivo com rotação
    try:
        Config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Erro ao configurar log de arquivo: {e}", file=sys.stderr)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para erros críticos (stderr)
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(console_formatter)
    logger.addHandler(error_handler)
    
    # Não propagar para o logger pai
    logger.propagate = False
    
    return logger


def setup_flask_logging(app):
    """
    Configura logging específico para Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Configurar logger do Werkzeug (servidor de desenvolvimento)
    werkzeug_logger = logging.getLogger('werkzeug')
    
    if app.config.get('DEBUG'):
        werkzeug_logger.setLevel(logging.INFO)
    else:
        werkzeug_logger.setLevel(logging.WARNING)
    
    # Configurar logger do Flask
    app.logger.handlers.clear()
    
    # Usar o mesmo sistema de logging
    flask_logger = setup_logger('flask_app', Config.LOG_LEVEL)
    
    # Copiar handlers para o logger do Flask
    for handler in flask_logger.handlers:
        app.logger.addHandler(handler)
    
    app.logger.setLevel(flask_logger.level)


def log_performance(func):
    """
    Decorator para medir performance de funções.
    
    Args:
        func: Função para decorar
        
    Returns:
        Função decorada
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.debug(f"Performance - {func.__name__}: {execution_time:.3f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Performance - {func.__name__}: {execution_time:.3f}s (ERRO: {str(e)})")
            raise
    
    return wrapper


def log_request(logger):
    """
    Decorator para logging de requisições.
    
    Args:
        logger: Logger para usar
        
    Returns:
        Decorator
    """
    def decorator(func):
        import functools
        from flask import request
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log da requisição
            logger.info(f"Requisição: {request.method} {request.path}")
            logger.debug(f"Headers: {dict(request.headers)}")
            
            if request.is_json:
                logger.debug(f"JSON payload: {request.get_json()}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Requisição concluída: {request.method} {request.path}")
                return result
                
            except Exception as e:
                logger.error(f"Erro na requisição {request.method} {request.path}: {str(e)}")
                raise
        
        return wrapper
    return decorator


class LoggingContext:
    """Context manager para logging com contexto adicional."""
    
    def __init__(self, logger, context_info: dict):
        self.logger = logger
        self.context_info = context_info
        self.original_format = None
    
    def __enter__(self):
        # Adicionar informações de contexto
        context_str = " | ".join([f"{k}={v}" for k, v in self.context_info.items()])
        
        for handler in self.logger.handlers:
            if hasattr(handler, 'formatter') and handler.formatter:
                original_format = handler.formatter._fmt
                new_format = original_format.replace(
                    '%(message)s',
                    f'[{context_str}] %(message)s'
                )
                handler.setFormatter(logging.Formatter(new_format))
        
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restaurar formato original (se necessário)
        pass


def get_logger(name: str) -> logging.Logger:
    """
    Função conveniente para obter um logger.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return setup_logger(name)


# Logger global para o módulo
logger = setup_logger(__name__)
