"""
Configurações do Sistema Automatizador de Diplomas

Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614

Este módulo contém todas as configurações da aplicação,
incluindo configurações de desenvolvimento, produção e testes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    """Configurações base da aplicação."""
    
    # Configurações gerais
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 'yes']
    TESTING = False
    
    # Configurações do servidor
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5001))
    
    # Configurações de CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:5001').split(',')
    
    # Configurações de upload
    BASE_DIR = Path(__file__).parent.parent
    UPLOAD_FOLDER = BASE_DIR / 'temp' / 'uploads'
    TEMP_FOLDER = BASE_DIR / 'temp'
    STATIC_FOLDER = BASE_DIR / 'static'
    
    # Limites de arquivo
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024))  # 100MB
    ALLOWED_EXTENSIONS = {'zip'}
    
    # Configurações do Moodle
    MOODLE_URL = os.getenv('MOODLE_URL', 'https://seu-moodle.exemplo.com')
    MOODLE_API_TOKEN = os.getenv('MOODLE_API_TOKEN', '')
    MOODLE_FUNCTION = 'local_diploma_data_get_user_diploma_details'
    MOODLE_TIMEOUT = int(os.getenv('MOODLE_TIMEOUT', 30))
    
    # Configurações de QR Code
    QR_CODE_SIZE = int(os.getenv('QR_CODE_SIZE', 200))
    QR_CODE_BORDER = int(os.getenv('QR_CODE_BORDER', 4))
    QR_CODE_VERSION = int(os.getenv('QR_CODE_VERSION', 1))
    
    # Configurações de verificação
    VERIFICATION_BASE_URL = os.getenv('VERIFICATION_BASE_URL', 'https://seu-dominio.com/api')
    
    # Configurações de log
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = BASE_DIR / 'logs' / 'app.log'
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Configurações de sessão
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hora em segundos
    SESSION_CLEANUP_INTERVAL = int(os.getenv('SESSION_CLEANUP_INTERVAL', 300))  # 5 minutos
    
    # Configurações de PDF
    PDF_DPI = int(os.getenv('PDF_DPI', 300))
    PDF_QUALITY = int(os.getenv('PDF_QUALITY', 95))
    
    # Padrões de extração de texto
    STUDENT_NAME_PATTERNS = [
        r'(?:Nome|Name):\s*([A-Za-zÀ-ÿ\s]+)',
        r'(?:Aluno|Student):\s*([A-Za-zÀ-ÿ\s]+)',
        r'(?:Formando|Graduate):\s*([A-Za-zÀ-ÿ\s]+)',
        r'([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)+)',  # Nome em formato título
    ]
    
    # Configurações de segurança
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
    RATE_LIMIT = os.getenv('RATE_LIMIT', '100 per hour')
    
    @classmethod
    def init_app(cls, app):
        """Inicializa configurações específicas da aplicação."""
        # Criar diretórios necessários
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Configurações para ambiente de produção."""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'
    
    # Configurações de segurança mais rígidas para produção
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Configurações para ambiente de testes."""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Usar diretórios temporários para testes
    UPLOAD_FOLDER = Config.BASE_DIR / 'temp' / 'test_uploads'
    TEMP_FOLDER = Config.BASE_DIR / 'temp' / 'test_temp'


# Mapeamento de ambientes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retorna a configuração baseada na variável de ambiente."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
