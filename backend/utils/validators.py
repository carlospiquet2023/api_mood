"""
Validadores do Sistema
Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614

Este módulo contém todas as validações necessárias para
uploads, dados de entrada e integridade do sistema.
"""

import os
import re
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import zipfile
import magic  # python-magic para detecção de tipo MIME

from config.settings import Config

logger = logging.getLogger(__name__)


class FileValidator:
    """Classe para validação de arquivos."""
    
    def __init__(self):
        """Inicializa o validador de arquivos."""
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        self.max_file_size = Config.MAX_FILE_SIZE
        
        logger.info("FileValidator inicializado")
    
    def validate_upload(self, file, max_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Valida arquivo de upload.
        
        Args:
            file: Arquivo do Flask (FileStorage)
            max_size: Tamanho máximo personalizado
            
        Returns:
            Dict com resultado da validação
        """
        try:
            max_size = max_size or self.max_file_size
            
            # Verificar se arquivo existe
            if not file or not file.filename:
                return {
                    'valid': False,
                    'error': 'Nenhum arquivo foi enviado'
                }
            
            filename = file.filename.lower()
            
            # Verificar extensão
            if not self._validate_extension(filename):
                return {
                    'valid': False,
                    'error': f'Extensão não permitida. Permitidas: {", ".join(self.allowed_extensions)}'
                }
            
            # Verificar tamanho
            size_validation = self._validate_file_size(file, max_size)
            if not size_validation['valid']:
                return size_validation
            
            # Verificar tipo MIME
            mime_validation = self._validate_mime_type(file)
            if not mime_validation['valid']:
                return mime_validation
            
            # Verificar nome do arquivo
            name_validation = self._validate_filename(file.filename)
            if not name_validation['valid']:
                return name_validation
            
            logger.info(f"Arquivo validado com sucesso: {file.filename}")
            
            return {
                'valid': True,
                'filename': file.filename,
                'size': self._get_file_size(file),
                'mime_type': self._get_mime_type(file)
            }
            
        except Exception as e:
            logger.error(f"Erro na validação de arquivo: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': 'Erro interno na validação do arquivo'
            }
    
    def validate_zip_content(self, zip_path: str) -> Dict[str, Any]:
        """
        Valida conteúdo de arquivo ZIP.
        
        Args:
            zip_path: Caminho para o arquivo ZIP
            
        Returns:
            Dict com resultado da validação
        """
        try:
            logger.info(f"Validando conteúdo do ZIP: {zip_path}")
            
            if not os.path.exists(zip_path):
                return {
                    'valid': False,
                    'error': 'Arquivo ZIP não encontrado'
                }
            
            # Verificar se é um ZIP válido
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Verificar integridade
                    bad_files = zip_ref.testzip()
                    if bad_files:
                        return {
                            'valid': False,
                            'error': f'Arquivo ZIP corrompido: {bad_files}'
                        }
                    
                    # Listar arquivos
                    file_list = zip_ref.namelist()
                    
                    if not file_list:
                        return {
                            'valid': False,
                            'error': 'Arquivo ZIP está vazio'
                        }
                    
                    # Validar arquivos individuais
                    pdf_files = []
                    invalid_files = []
                    
                    for filename in file_list:
                        if self._is_valid_zip_entry(filename):
                            if filename.lower().endswith('.pdf'):
                                pdf_files.append(filename)
                        else:
                            invalid_files.append(filename)
                    
                    if not pdf_files:
                        return {
                            'valid': False,
                            'error': 'Nenhum arquivo PDF válido encontrado no ZIP'
                        }
                    
                    # Verificar tamanho dos arquivos
                    total_size = sum(zip_ref.getinfo(name).file_size for name in pdf_files)
                    
                    if total_size > self.max_file_size * 10:  # 10x o limite para descompactado
                        return {
                            'valid': False,
                            'error': 'Conteúdo do ZIP muito grande'
                        }
                    
                    logger.info(f"ZIP validado: {len(pdf_files)} PDFs encontrados")
                    
                    return {
                        'valid': True,
                        'pdf_count': len(pdf_files),
                        'pdf_files': pdf_files,
                        'invalid_files': invalid_files,
                        'total_size': total_size
                    }
                    
            except zipfile.BadZipFile:
                return {
                    'valid': False,
                    'error': 'Arquivo não é um ZIP válido'
                }
                
        except Exception as e:
            logger.error(f"Erro na validação do ZIP: {str(e)}", exc_info=True)
            return {
                'valid': False,
                'error': 'Erro interno na validação do ZIP'
            }
    
    def validate_coordinates(self, coords: Dict) -> Dict[str, Any]:
        """
        Valida coordenadas para inserção de QR code.
        
        Args:
            coords: Dicionário com coordenadas {x, y}
            
        Returns:
            Dict com resultado da validação
        """
        try:
            required_fields = ['x', 'y']
            
            for field in required_fields:
                if field not in coords:
                    return {
                        'valid': False,
                        'error': f'Campo obrigatório ausente: {field}'
                    }
            
            # Validar se são números
            try:
                x = float(coords['x'])
                y = float(coords['y'])
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error': 'Coordenadas devem ser números válidos'
                }
            
            # Validar limites razoáveis (em pontos PDF)
            if x < 0 or x > 2000 or y < 0 or y > 2000:
                return {
                    'valid': False,
                    'error': 'Coordenadas fora dos limites válidos'
                }
            
            return {
                'valid': True,
                'x': x,
                'y': y
            }
            
        except Exception as e:
            logger.error(f"Erro na validação de coordenadas: {str(e)}")
            return {
                'valid': False,
                'error': 'Erro interno na validação das coordenadas'
            }
    
    def _validate_extension(self, filename: str) -> bool:
        """Valida extensão do arquivo."""
        return any(filename.endswith(ext) for ext in self.allowed_extensions)
    
    def _validate_file_size(self, file, max_size: int) -> Dict[str, Any]:
        """Valida tamanho do arquivo."""
        try:
            # Obter tamanho do arquivo
            file.seek(0, 2)  # Ir para o final
            size = file.tell()
            file.seek(0)     # Voltar ao início
            
            if size > max_size:
                size_mb = size / (1024 * 1024)
                max_mb = max_size / (1024 * 1024)
                
                return {
                    'valid': False,
                    'error': f'Arquivo muito grande: {size_mb:.1f}MB. Máximo permitido: {max_mb:.1f}MB'
                }
            
            if size == 0:
                return {
                    'valid': False,
                    'error': 'Arquivo está vazio'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Erro ao validar tamanho: {str(e)}")
            return {
                'valid': False,
                'error': 'Erro ao verificar tamanho do arquivo'
            }
    
    def _validate_mime_type(self, file) -> Dict[str, Any]:
        """Valida tipo MIME do arquivo."""
        try:
            # Ler início do arquivo para detecção de tipo
            file.seek(0)
            file_header = file.read(1024)
            file.seek(0)
            
            # Detectar tipo MIME
            try:
                mime_type = magic.from_buffer(file_header, mime=True)
            except:
                # Fallback para mimetypes
                mime_type, _ = mimetypes.guess_type(file.filename)
            
            # Verificar se é um tipo permitido
            allowed_mimes = [
                'application/zip',
                'application/x-zip-compressed',
                'multipart/x-zip'
            ]
            
            if mime_type not in allowed_mimes:
                return {
                    'valid': False,
                    'error': f'Tipo de arquivo não permitido: {mime_type}'
                }
            
            return {'valid': True, 'mime_type': mime_type}
            
        except Exception as e:
            logger.error(f"Erro na validação de MIME: {str(e)}")
            # Em caso de erro, permitir (não bloquear)
            return {'valid': True}
    
    def _validate_filename(self, filename: str) -> Dict[str, Any]:
        """Valida nome do arquivo."""
        try:
            # Verificar caracteres perigosos
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
            if any(char in filename for char in dangerous_chars):
                return {
                    'valid': False,
                    'error': 'Nome do arquivo contém caracteres inválidos'
                }
            
            # Verificar comprimento
            if len(filename) > 255:
                return {
                    'valid': False,
                    'error': 'Nome do arquivo muito longo'
                }
            
            # Verificar se não é apenas espaços
            if not filename.strip():
                return {
                    'valid': False,
                    'error': 'Nome do arquivo inválido'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Erro na validação do nome: {str(e)}")
            return {'valid': True}  # Não bloquear em caso de erro
    
    def _get_file_size(self, file) -> int:
        """Obtém tamanho do arquivo."""
        try:
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            return size
        except:
            return 0
    
    def _get_mime_type(self, file) -> str:
        """Obtém tipo MIME do arquivo."""
        try:
            file.seek(0)
            file_header = file.read(1024)
            file.seek(0)
            
            try:
                return magic.from_buffer(file_header, mime=True)
            except:
                mime_type, _ = mimetypes.guess_type(file.filename)
                return mime_type or 'application/octet-stream'
        except:
            return 'application/octet-stream'
    
    def _is_valid_zip_entry(self, filename: str) -> bool:
        """Verifica se entrada do ZIP é válida."""
        # Ignorar diretórios
        if filename.endswith('/'):
            return False
        
        # Ignorar arquivos de sistema
        system_files = [
            '__MACOSX',
            '.DS_Store',
            'Thumbs.db',
            'desktop.ini'
        ]
        
        if any(sys_file in filename for sys_file in system_files):
            return False
        
        # Ignorar arquivos ocultos
        if filename.startswith('.'):
            return False
        
        return True


class DataValidator:
    """Classe para validação de dados de entrada."""
    
    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Valida formato do ID de sessão."""
        if not session_id or not isinstance(session_id, str):
            return False
        
        # Verificar formato (letras, números, hífens)
        if not re.match(r'^[a-zA-Z0-9\-]{10,50}$', session_id):
            return False
        
        return True
    
    @staticmethod
    def validate_student_name(name: str) -> Dict[str, Any]:
        """Valida nome do estudante."""
        if not name or not isinstance(name, str):
            return {
                'valid': False,
                'error': 'Nome é obrigatório'
            }
        
        name = name.strip()
        
        if len(name) < 3:
            return {
                'valid': False,
                'error': 'Nome muito curto'
            }
        
        if len(name) > 100:
            return {
                'valid': False,
                'error': 'Nome muito longo'
            }
        
        # Verificar se contém apenas letras e espaços
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', name):
            return {
                'valid': False,
                'error': 'Nome contém caracteres inválidos'
            }
        
        return {
            'valid': True,
            'normalized_name': ' '.join(name.split())  # Normalizar espaços
        }
    
    @staticmethod
    def validate_qr_size(size: Any) -> Dict[str, Any]:
        """Valida tamanho do QR code."""
        try:
            size = int(size)
            
            if size < 50 or size > 500:
                return {
                    'valid': False,
                    'error': 'Tamanho do QR code deve estar entre 50 e 500 pixels'
                }
            
            return {
                'valid': True,
                'size': size
            }
            
        except (ValueError, TypeError):
            return {
                'valid': False,
                'error': 'Tamanho do QR code deve ser um número'
            }
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email."""
        if not email or not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitiza entrada de texto."""
        if not isinstance(input_str, str):
            return str(input_str)
        
        # Remover caracteres perigosos
        dangerous_chars = ['<', '>', '"', "'", '&', '\0']
        sanitized = input_str
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Normalizar espaços
        sanitized = ' '.join(sanitized.split())
        
        return sanitized.strip()
