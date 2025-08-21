"""
Gerador de QR Codes
Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614

Este módulo é responsável pela geração de QR codes personalizados
para os diplomas, incluindo dados de verificação e formatação.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image, ImageDraw, ImageFont
import hashlib

from config.settings import Config

logger = logging.getLogger(__name__)


class QRGenerator:
    """Classe responsável pela geração de QR codes."""
    
    def __init__(self):
        """Inicializa o gerador de QR codes."""
        self.qr_size = Config.QR_CODE_SIZE
        self.border = Config.QR_CODE_BORDER
        self.version = Config.QR_CODE_VERSION
        
        # Diretório temporário para QR codes
        self.temp_dir = Path(tempfile.gettempdir()) / 'diploma_qr_codes'
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info("QRGenerator inicializado")
    
    def generate_qr_code(self, diploma_data: Dict[str, Any], session_id: str) -> str:
        """
        Gera QR code com dados do diploma.
        
        Args:
            diploma_data: Dados para incluir no QR code
            session_id: ID da sessão
            
        Returns:
            Caminho para o arquivo de imagem do QR code
        """
        try:
            logger.info(f"Gerando QR code para estudante: {diploma_data.get('student_name')}")
            
            # Preparar dados para o QR code
            qr_content = self._prepare_qr_content(diploma_data)
            
            # Criar QR code
            qr = qrcode.QRCode(
                version=self.version,
                error_correction=ERROR_CORRECT_M,
                box_size=10,
                border=self.border,
            )
            
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Criar imagem
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionar para o tamanho desejado
            qr_image = qr_image.resize((self.qr_size, self.qr_size), Image.LANCZOS)
            
            # Adicionar elementos visuais personalizados se necessário
            qr_image = self._customize_qr_image(qr_image, diploma_data)
            
            # Salvar imagem
            qr_dir = self.temp_dir / f"qr_{session_id}"
            qr_dir.mkdir(exist_ok=True)
            
            # Nome do arquivo baseado no hash dos dados
            file_hash = self._generate_file_hash(qr_content)
            qr_path = qr_dir / f"qr_{file_hash}.png"
            
            qr_image.save(str(qr_path), "PNG", quality=95, optimize=True)
            
            logger.info(f"QR code gerado: {qr_path}")
            return str(qr_path)
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code: {str(e)}", exc_info=True)
            raise
    
    def generate_verification_qr(self, verification_url: str, session_id: str) -> str:
        """
        Gera QR code simples apenas com URL de verificação.
        
        Args:
            verification_url: URL para verificação do diploma
            session_id: ID da sessão
            
        Returns:
            Caminho para o arquivo de imagem do QR code
        """
        try:
            logger.info(f"Gerando QR code de verificação: {verification_url}")
            
            # Criar QR code simples
            qr = qrcode.QRCode(
                version=1,
                error_correction=ERROR_CORRECT_M,
                box_size=10,
                border=self.border,
            )
            
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Criar imagem
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image = qr_image.resize((self.qr_size, self.qr_size), Image.LANCZOS)
            
            # Salvar imagem
            qr_dir = self.temp_dir / f"qr_{session_id}"
            qr_dir.mkdir(exist_ok=True)
            
            file_hash = hashlib.md5(verification_url.encode()).hexdigest()[:8]
            qr_path = qr_dir / f"verification_qr_{file_hash}.png"
            
            qr_image.save(str(qr_path), "PNG", quality=95, optimize=True)
            
            logger.info(f"QR code de verificação gerado: {qr_path}")
            return str(qr_path)
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code de verificação: {str(e)}", exc_info=True)
            raise
    
    def _prepare_qr_content(self, diploma_data: Dict[str, Any]) -> str:
        """
        Prepara o conteúdo do QR code.
        
        Args:
            diploma_data: Dados do diploma
            
        Returns:
            String formatada para o QR code
        """
        try:
            # Opção 1: URL de verificação simples
            if 'verification_url' in diploma_data:
                return diploma_data['verification_url']
            
            # Opção 2: JSON estruturado (para mais dados)
            qr_data = {
                'type': 'diploma_verification',
                'version': '1.0',
                'student': {
                    'id': diploma_data.get('student_id'),
                    'name': diploma_data.get('student_name'),
                    'email': diploma_data.get('student_email')
                },
                'course': {
                    'id': diploma_data.get('course_id')
                },
                'issued': diploma_data.get('issued_date'),
                'verify_url': diploma_data.get('verification_url', '')
            }
            
            # Compactar JSON para economizar espaço no QR
            json_content = json.dumps(qr_data, separators=(',', ':'), ensure_ascii=False)
            
            logger.debug(f"Conteúdo do QR code: {json_content[:100]}...")
            return json_content
            
        except Exception as e:
            logger.error(f"Erro ao preparar conteúdo do QR: {str(e)}")
            # Fallback para URL simples
            return diploma_data.get('verification_url', '')
    
    def _customize_qr_image(self, qr_image: Image.Image, diploma_data: Dict[str, Any]) -> Image.Image:
        """
        Personaliza a imagem do QR code com elementos visuais.
        
        Args:
            qr_image: Imagem base do QR code
            diploma_data: Dados do diploma
            
        Returns:
            Imagem customizada
        """
        try:
            # Converter para RGB se necessário
            if qr_image.mode != 'RGB':
                qr_image = qr_image.convert('RGB')
            
            # Criar nova imagem com espaço para texto (opcional)
            img_width, img_height = qr_image.size
            
            # Por enquanto, retornar a imagem original
            # Você pode adicionar customizações aqui, como:
            # - Logo no centro
            # - Texto informativo
            # - Bordas coloridas
            
            return qr_image
            
        except Exception as e:
            logger.error(f"Erro ao customizar QR image: {str(e)}")
            return qr_image
    
    def _add_logo_to_qr(self, qr_image: Image.Image, logo_path: str) -> Image.Image:
        """
        Adiciona logo no centro do QR code.
        
        Args:
            qr_image: Imagem do QR code
            logo_path: Caminho para o logo
            
        Returns:
            Imagem com logo
        """
        try:
            if not Path(logo_path).exists():
                return qr_image
            
            # Abrir logo
            logo = Image.open(logo_path)
            
            # Calcular tamanho do logo (não deve ser muito grande)
            qr_width, qr_height = qr_image.size
            logo_size = min(qr_width // 5, qr_height // 5)  # 20% do tamanho do QR
            
            # Redimensionar logo
            logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
            
            # Calcular posição central
            logo_pos = (
                (qr_width - logo_size) // 2,
                (qr_height - logo_size) // 2
            )
            
            # Criar máscara se o logo tem transparência
            if logo.mode == 'RGBA':
                qr_image.paste(logo, logo_pos, logo)
            else:
                qr_image.paste(logo, logo_pos)
            
            return qr_image
            
        except Exception as e:
            logger.error(f"Erro ao adicionar logo ao QR: {str(e)}")
            return qr_image
    
    def _add_text_to_qr(self, qr_image: Image.Image, text: str, position: str = 'bottom') -> Image.Image:
        """
        Adiciona texto informativo à imagem do QR code.
        
        Args:
            qr_image: Imagem do QR code
            text: Texto para adicionar
            position: Posição do texto ('top', 'bottom')
            
        Returns:
            Imagem com texto
        """
        try:
            # Calcular dimensões
            img_width, img_height = qr_image.size
            text_height = 30  # Altura da área de texto
            
            # Criar nova imagem com espaço para texto
            if position == 'bottom':
                new_height = img_height + text_height
                new_image = Image.new('RGB', (img_width, new_height), 'white')
                new_image.paste(qr_image, (0, 0))
                text_y = img_height + 5
            else:  # top
                new_height = img_height + text_height
                new_image = Image.new('RGB', (img_width, new_height), 'white')
                new_image.paste(qr_image, (0, text_height))
                text_y = 5
            
            # Adicionar texto
            draw = ImageDraw.Draw(new_image)
            
            # Tentar carregar fonte
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except OSError:
                font = ImageFont.load_default()
            
            # Calcular posição central do texto
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (img_width - text_width) // 2
            
            # Desenhar texto
            draw.text((text_x, text_y), text, fill='black', font=font)
            
            return new_image
            
        except Exception as e:
            logger.error(f"Erro ao adicionar texto ao QR: {str(e)}")
            return qr_image
    
    def _generate_file_hash(self, content: str) -> str:
        """
        Gera hash único para o conteúdo.
        
        Args:
            content: Conteúdo para gerar hash
            
        Returns:
            Hash MD5 truncado
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
    
    def validate_qr_content(self, content: str) -> bool:
        """
        Valida se o conteúdo é adequado para QR code.
        
        Args:
            content: Conteúdo para validar
            
        Returns:
            True se válido
        """
        try:
            # Verificar tamanho (QR codes têm limites)
            if len(content) > 2000:  # Limite conservador
                logger.warning(f"Conteúdo muito longo para QR code: {len(content)} caracteres")
                return False
            
            # Tentar criar QR code de teste
            test_qr = qrcode.QRCode(version=self.version)
            test_qr.add_data(content)
            test_qr.make(fit=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Conteúdo inválido para QR code: {str(e)}")
            return False
    
    def cleanup_session_qr_codes(self, session_id: str):
        """
        Remove QR codes temporários da sessão.
        
        Args:
            session_id: ID da sessão para limpeza
        """
        try:
            logger.info(f"Limpando QR codes da sessão: {session_id}")
            
            qr_dir = self.temp_dir / f"qr_{session_id}"
            if qr_dir.exists():
                import shutil
                shutil.rmtree(qr_dir)
                logger.debug(f"Diretório de QR codes removido: {qr_dir}")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de QR codes da sessão {session_id}: {str(e)}")
    
    def get_qr_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas sobre QR codes gerados.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            qr_files = list(self.temp_dir.glob("**/*.png"))
            total_files = len(qr_files)
            
            # Calcular tamanho total
            total_size = sum(f.stat().st_size for f in qr_files if f.exists())
            
            return {
                'total_qr_codes': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'temp_directory': str(self.temp_dir)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de QR: {str(e)}")
            return {}
