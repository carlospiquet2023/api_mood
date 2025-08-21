"""
Sistema Automatizador de Diplomas com QR Code
Aplicação Flask Principal

Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614
Versão: 1.0.0
Data: 2025-08-20

Descrição:
    Backend Flask robusto para automatização de diplomas com QR Code.
    Integra com Moodle para obter dados dos estudantes e processa
    diplomas em lote com inserção automática de QR Codes.
"""

import os
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Importações dos serviços customizados
from config.settings import Config
from services.pdf_processor import PDFProcessor
from services.moodle_client_simple import MoodleClient
from services.qr_generator import QRGenerator
from utils.logger import setup_logger
from utils.validators import FileValidator
from utils.session_manager import SessionManager

# Configuração da aplicação Flask
app = Flask(__name__)
app.config.from_object(Config)

# Configuração CORS para desenvolvimento seguro
CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000', 'http://127.0.0.1:5001']))

# Configuração de logging
logger = setup_logger(__name__)

# Inicialização dos serviços
pdf_processor = PDFProcessor()
moodle_client = MoodleClient()
qr_generator = QRGenerator()
file_validator = FileValidator()
session_manager = SessionManager()

# Configurações de upload
UPLOAD_FOLDER = Path(app.config['UPLOAD_FOLDER'])
TEMP_FOLDER = Path(app.config['TEMP_FOLDER'])
MAX_FILE_SIZE = app.config['MAX_FILE_SIZE']
ALLOWED_EXTENSIONS = app.config['ALLOWED_EXTENSIONS']

# Garantir que as pastas existem
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)


@app.route('/')
def index():
    """Página principal da aplicação."""
    try:
        logger.info("Acesso à página principal")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erro ao carregar página principal: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir arquivos estáticos."""
    return send_from_directory('static', filename)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint para verificação de saúde da aplicação."""
    try:
        # Verificar conectividade com Moodle
        moodle_status = moodle_client.check_connection()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {
                'moodle': 'connected' if moodle_status else 'disconnected',
                'pdf_processor': 'active',
                'qr_generator': 'active'
            }
        }
        
        status_code = 200 if moodle_status else 503
        logger.info(f"Health check - Status: {health_data['status']}")
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para upload de arquivo ZIP com diplomas.
    
    Returns:
        JSON: Dados da sessão e preview do primeiro PDF
    """
    try:
        logger.info("Iniciando upload de arquivo")
        
        # Validar se arquivo foi enviado
        if 'file' not in request.files:
            logger.warning("Nenhum arquivo enviado na requisição")
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.warning("Nome de arquivo vazio")
            return jsonify({'error': 'Nome de arquivo inválido'}), 400
        
        # Validar arquivo
        validation_result = file_validator.validate_upload(file, MAX_FILE_SIZE)
        if not validation_result['valid']:
            logger.warning(f"Arquivo inválido: {validation_result['error']}")
            return jsonify({'error': validation_result['error']}), 400
        
        # Gerar ID de sessão único
        session_id = session_manager.create_session()
        logger.info(f"Sessão criada: {session_id}")
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        file_path = UPLOAD_FOLDER / f"{session_id}_{filename}"
        file.save(str(file_path))
        
        logger.info(f"Arquivo salvo: {file_path}")
        
        # Processar arquivo ZIP
        extraction_result = pdf_processor.extract_zip(str(file_path), session_id)
        
        if not extraction_result['success']:
            logger.error(f"Erro ao extrair ZIP: {extraction_result['error']}")
            return jsonify({'error': extraction_result['error']}), 400
        
        # Obter primeiro PDF para preview
        first_pdf_path = extraction_result['first_pdf']
        pdf_data = pdf_processor.get_pdf_base64(first_pdf_path)
        
        # Armazenar dados da sessão
        session_data = {
            'zip_path': str(file_path),
            'extracted_folder': extraction_result['extract_path'],
            'pdf_files': extraction_result['pdf_files'],
            'total_files': len(extraction_result['pdf_files']),
            'created_at': datetime.utcnow().isoformat()
        }
        
        session_manager.store_session_data(session_id, session_data)
        
        logger.info(f"Upload processado com sucesso. {session_data['total_files']} PDFs encontrados")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'total_files': session_data['total_files'],
            'first_pdf_b64': pdf_data,
            'message': f'Upload realizado com sucesso. {session_data["total_files"]} diplomas encontrados.'
        })
        
    except Exception as e:
        logger.error(f"Erro no upload: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno no processamento do arquivo'}), 500


@app.route('/api/process-files', methods=['POST'])
def process_files():
    """
    Endpoint para processar diplomas com QR Codes.
    
    Returns:
        FILE: ZIP com diplomas processados
    """
    try:
        data = request.get_json()
        
        # Validar dados de entrada
        required_fields = ['session_id', 'qr_coords', 'qr_size']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório ausente: {field}'}), 400
        
        session_id = data['session_id']
        qr_coords = data['qr_coords']
        qr_size = data['qr_size']
        
        logger.info(f"Iniciando processamento para sessão: {session_id}")
        
        # Recuperar dados da sessão
        session_data = session_manager.get_session_data(session_id)
        if not session_data:
            logger.warning(f"Sessão não encontrada: {session_id}")
            return jsonify({'error': 'Sessão não encontrada ou expirada'}), 404
        
        # Processar cada diploma
        processed_files = []
        errors = []
        
        for i, pdf_path in enumerate(session_data['pdf_files']):
            try:
                logger.info(f"Processando diploma {i+1}/{len(session_data['pdf_files'])}: {pdf_path}")
                
                # Extrair nome do estudante do PDF
                student_name = pdf_processor.extract_student_name(pdf_path)
                if not student_name:
                    logger.warning(f"Nome do estudante não encontrado no arquivo: {pdf_path}")
                    errors.append(f"Nome não encontrado: {os.path.basename(pdf_path)}")
                    continue
                
                logger.info(f"Nome extraído: {student_name}")
                
                # Buscar dados do estudante no Moodle
                student_data = moodle_client.get_student_data(student_name)
                if not student_data:
                    logger.warning(f"Dados do estudante não encontrados no Moodle: {student_name}")
                    errors.append(f"Estudante não encontrado no Moodle: {student_name}")
                    continue
                
                # Gerar QR Code
                qr_data = {
                    'student_id': student_data.get('id'),
                    'student_name': student_name,
                    'student_email': student_data.get('email'),
                    'course_id': student_data.get('course_id'),
                    'issued_date': datetime.utcnow().isoformat(),
                    'verification_url': f"{app.config['VERIFICATION_BASE_URL']}/verify/{session_id}/{student_data.get('id')}"
                }
                
                qr_image_path = qr_generator.generate_qr_code(qr_data, session_id)
                
                # Inserir QR Code no PDF
                output_path = pdf_processor.insert_qr_code(
                    pdf_path, 
                    qr_image_path, 
                    qr_coords, 
                    qr_size,
                    session_id
                )
                
                processed_files.append(output_path)
                logger.info(f"Diploma processado com sucesso: {output_path}")
                
            except Exception as e:
                error_msg = f"Erro ao processar {os.path.basename(pdf_path)}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        if not processed_files:
            logger.error("Nenhum diploma foi processado com sucesso")
            return jsonify({
                'error': 'Nenhum diploma foi processado com sucesso',
                'details': errors
            }), 400
        
        # Criar ZIP com arquivos processados
        output_zip_path = pdf_processor.create_output_zip(processed_files, session_id)
        
        logger.info(f"Processamento concluído. {len(processed_files)} diplomas processados")
        
        # Limpar sessão após sucesso
        session_manager.cleanup_session(session_id)
        
        return send_file(
            output_zip_path,
            as_attachment=True,
            download_name=f'diplomas_processados_{session_id}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno no processamento'}), 500


@app.route('/api/verify/<session_id>/<student_id>', methods=['GET'])
def verify_diploma(session_id: str, student_id: str):
    """
    Endpoint para verificação de autenticidade do diploma.
    
    Args:
        session_id: ID da sessão de processamento
        student_id: ID do estudante
        
    Returns:
        JSON: Dados de verificação do diploma
    """
    try:
        logger.info(f"Verificação solicitada - Sessão: {session_id}, Estudante: {student_id}")
        
        # Verificar dados no Moodle
        verification_data = moodle_client.verify_diploma(student_id, session_id)
        
        if verification_data:
            logger.info(f"Diploma verificado com sucesso para estudante: {student_id}")
            return jsonify({
                'valid': True,
                'student_data': verification_data,
                'verified_at': datetime.utcnow().isoformat(),
                'message': 'Diploma autêntico e válido'
            })
        else:
            logger.warning(f"Diploma não verificado para estudante: {student_id}")
            return jsonify({
                'valid': False,
                'message': 'Diploma não encontrado ou inválido'
            }), 404
            
    except Exception as e:
        logger.error(f"Erro na verificação: {str(e)}", exc_info=True)
        return jsonify({
            'valid': False,
            'error': 'Erro interno na verificação'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handler para erro 404."""
    logger.warning(f"Endpoint não encontrado: {request.url}")
    return jsonify({'error': 'Endpoint não encontrado'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para erro 500."""
    logger.error(f"Erro interno do servidor: {str(error)}", exc_info=True)
    return jsonify({'error': 'Erro interno do servidor'}), 500


@app.before_request
def log_request_info():
    """Log de informações da requisição."""
    if not request.path.startswith('/static'):
        logger.info(f"Requisição: {request.method} {request.path} - IP: {request.remote_addr}")


@app.after_request
def log_response_info(response):
    """Log de informações da resposta."""
    if not request.path.startswith('/static'):
        logger.info(f"Resposta: {response.status_code} para {request.method} {request.path}")
    return response


if __name__ == '__main__':
    # Limpeza de sessões expiradas na inicialização
    session_manager.cleanup_expired_sessions()
    
    logger.info("=== Sistema Automatizador de Diplomas ===")
    logger.info("Iniciando servidor Flask...")
    logger.info(f"Versão: 1.0.0")
    logger.info(f"Ambiente: {app.config.get('ENV', 'development')}")
    logger.info(f"Debug: {app.config.get('DEBUG', False)}")
    logger.info(f"Host: {app.config.get('HOST', '127.0.0.1')}")
    logger.info(f"Porta: {app.config.get('PORT', 5001)}")
    
    app.run(
        host=app.config.get('HOST', '127.0.0.1'),
        port=app.config.get('PORT', 5001),
        debug=app.config.get('DEBUG', False),
        threaded=True
    )
