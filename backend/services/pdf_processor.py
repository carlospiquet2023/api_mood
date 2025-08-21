"""
Serviço de Processamento de PDFs
Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614

Este módulo contém todas as funcionalidades relacionadas ao processamento
de arquivos PDF, incluindo extração de texto, inserção de QR codes e
manipulação de arquivos ZIP.
"""

import os
import re
import base64
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Classe responsável pelo processamento de arquivos PDF."""
    
    def __init__(self):
        """Inicializa o processador de PDF."""
        self.supported_formats = ['.pdf']
        self.temp_dir = Path(tempfile.gettempdir()) / 'diploma_processor'
        self.temp_dir.mkdir(exist_ok=True)
        logger.info("PDFProcessor inicializado")
    
    def extract_zip(self, zip_path: str, session_id: str) -> Dict:
        """
        Extrai arquivos PDF de um arquivo ZIP.
        
        Args:
            zip_path: Caminho para o arquivo ZIP
            session_id: ID da sessão
            
        Returns:
            Dict com resultado da extração
        """
        try:
            logger.info(f"Extraindo ZIP: {zip_path}")
            
            # Criar diretório de extração
            extract_dir = self.temp_dir / f"session_{session_id}"
            extract_dir.mkdir(exist_ok=True)
            
            pdf_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Listar arquivos no ZIP
                file_list = zip_ref.namelist()
                logger.info(f"Arquivos encontrados no ZIP: {len(file_list)}")
                
                for file_name in file_list:
                    # Verificar se é um arquivo PDF válido
                    if self._is_valid_pdf_file(file_name):
                        # Extrair arquivo
                        zip_ref.extract(file_name, extract_dir)
                        
                        # Caminho completo do arquivo extraído
                        extracted_path = extract_dir / file_name
                        
                        # Validar se o PDF não está corrompido
                        if self._validate_pdf_file(str(extracted_path)):
                            pdf_files.append(str(extracted_path))
                            logger.debug(f"PDF extraído: {file_name}")
                        else:
                            logger.warning(f"PDF corrompido ignorado: {file_name}")
            
            if not pdf_files:
                logger.error("Nenhum arquivo PDF válido encontrado no ZIP")
                return {
                    'success': False,
                    'error': 'Nenhum arquivo PDF válido encontrado no ZIP'
                }
            
            # Ordenar arquivos para processamento consistente
            pdf_files.sort()
            
            logger.info(f"Extração concluída: {len(pdf_files)} PDFs válidos")
            
            return {
                'success': True,
                'extract_path': str(extract_dir),
                'pdf_files': pdf_files,
                'first_pdf': pdf_files[0] if pdf_files else None
            }
            
        except zipfile.BadZipFile:
            logger.error(f"Arquivo ZIP corrompido: {zip_path}")
            return {
                'success': False,
                'error': 'Arquivo ZIP corrompido ou inválido'
            }
        except Exception as e:
            logger.error(f"Erro ao extrair ZIP: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Erro ao processar arquivo ZIP: {str(e)}'
            }
    
    def get_pdf_base64(self, pdf_path: str) -> str:
        """
        Converte PDF para base64 para preview no frontend.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            String base64 do PDF
        """
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                return base64.b64encode(pdf_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao converter PDF para base64: {str(e)}")
            return ""
    
    def extract_student_name(self, pdf_path: str) -> Optional[str]:
        """
        Extrai o nome do estudante do texto do PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Nome do estudante ou None se não encontrado
        """
        try:
            logger.info(f"Extraindo nome do estudante de: {pdf_path}")
            
            # Abrir documento PDF
            doc = fitz.open(pdf_path)
            
            # Extrair texto de todas as páginas
            full_text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                full_text += text + "\n"
            
            doc.close()
            
            logger.debug(f"Texto extraído (primeiros 200 chars): {full_text[:200]}...")
            
            # Padrões para encontrar o nome do estudante
            patterns = [
                # Padrão: "Nome: João Silva"
                r'(?:Nome|Name):\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|$|[A-Z][a-z])',
                
                # Padrão: "Aluno: João Silva"
                r'(?:Aluno|Student|Estudante):\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|$|[A-Z][a-z])',
                
                # Padrão: "Formando: João Silva"
                r'(?:Formando|Graduate|Graduando):\s*([A-Za-zÀ-ÿ\s]+?)(?:\n|$|[A-Z][a-z])',
                
                # Padrão: Texto em maiúsculas (comum em diplomas)
                r'([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-zÀ-ÿ\s]+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][A-Za-zÀ-ÿ]+)',
                
                # Padrão: Nome próprio em formato título
                r'([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)+)',
                
                # Padrão específico para diplomas brasileiros
                r'(?:confere a|outorga a|concede a)\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+o|,)',
                
                # Padrão para encontrar nomes entre vírgulas ou pontos
                r',\s*([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)+)\s*,',
            ]
            
            found_names = []
            
            for pattern in patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    name = match.group(1).strip()
                    
                    # Validar se é um nome válido
                    if self._is_valid_name(name):
                        found_names.append(name)
                        logger.debug(f"Nome encontrado com padrão '{pattern}': {name}")
            
            if found_names:
                # Retornar o nome mais provável (mais longo e com mais palavras)
                best_name = max(found_names, key=lambda x: (len(x.split()), len(x)))
                logger.info(f"Nome selecionado: {best_name}")
                return best_name.title()  # Formatar em título
            
            logger.warning(f"Nome do estudante não encontrado em: {pdf_path}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair nome do PDF: {str(e)}", exc_info=True)
            return None
    
    def insert_qr_code(self, pdf_path: str, qr_image_path: str, 
                      coords: Dict, size: int, session_id: str) -> str:
        """
        Insere QR code no PDF nas coordenadas especificadas.
        
        Args:
            pdf_path: Caminho para o PDF original
            qr_image_path: Caminho para a imagem do QR code
            coords: Coordenadas {x, y} para inserção
            size: Tamanho do QR code em pontos
            session_id: ID da sessão
            
        Returns:
            Caminho para o PDF modificado
        """
        try:
            logger.info(f"Inserindo QR code em: {pdf_path}")
            
            # Abrir documento PDF
            doc = fitz.open(pdf_path)
            
            # Trabalhar com a primeira página (assumindo que é onde vai o QR)
            page = doc.load_page(0)
            
            # Converter coordenadas para o sistema do PyMuPDF
            # Coordenadas recebidas estão em pontos PDF (origem inferior esquerda)
            # PyMuPDF usa origem superior esquerda
            page_rect = page.rect
            x = coords['x']
            y = page_rect.height - coords['y']  # Inverter Y
            
            # Definir retângulo para inserção do QR code
            qr_rect = fitz.Rect(x, y - size, x + size, y)
            
            logger.debug(f"Coordenadas de inserção: x={x}, y={y}, size={size}")
            logger.debug(f"Retângulo QR: {qr_rect}")
            
            # Inserir imagem do QR code
            page.insert_image(qr_rect, filename=qr_image_path)
            
            # Criar arquivo de saída
            output_dir = self.temp_dir / f"output_{session_id}"
            output_dir.mkdir(exist_ok=True)
            
            original_name = Path(pdf_path).stem
            output_path = output_dir / f"{original_name}_com_qr.pdf"
            
            # Salvar PDF modificado
            doc.save(str(output_path))
            doc.close()
            
            logger.info(f"QR code inserido com sucesso: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Erro ao inserir QR code: {str(e)}", exc_info=True)
            raise
    
    def create_output_zip(self, pdf_files: List[str], session_id: str) -> str:
        """
        Cria arquivo ZIP com os PDFs processados.
        
        Args:
            pdf_files: Lista de caminhos para os PDFs processados
            session_id: ID da sessão
            
        Returns:
            Caminho para o arquivo ZIP criado
        """
        try:
            logger.info(f"Criando ZIP de saída para {len(pdf_files)} arquivos")
            
            output_zip_path = self.temp_dir / f"diplomas_processados_{session_id}.zip"
            
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for pdf_path in pdf_files:
                    # Nome do arquivo no ZIP (sem o caminho completo)
                    archive_name = Path(pdf_path).name
                    zipf.write(pdf_path, archive_name)
                    logger.debug(f"Adicionado ao ZIP: {archive_name}")
            
            logger.info(f"ZIP criado com sucesso: {output_zip_path}")
            return str(output_zip_path)
            
        except Exception as e:
            logger.error(f"Erro ao criar ZIP de saída: {str(e)}", exc_info=True)
            raise
    
    def cleanup_session_files(self, session_id: str):
        """
        Remove arquivos temporários da sessão.
        
        Args:
            session_id: ID da sessão para limpeza
        """
        try:
            logger.info(f"Limpando arquivos da sessão: {session_id}")
            
            session_dirs = [
                self.temp_dir / f"session_{session_id}",
                self.temp_dir / f"output_{session_id}",
                self.temp_dir / f"qr_{session_id}"
            ]
            
            for session_dir in session_dirs:
                if session_dir.exists():
                    import shutil
                    shutil.rmtree(session_dir)
                    logger.debug(f"Diretório removido: {session_dir}")
            
            # Remover arquivos ZIP da sessão
            for zip_file in self.temp_dir.glob(f"*{session_id}*.zip"):
                zip_file.unlink()
                logger.debug(f"Arquivo ZIP removido: {zip_file}")
                
            logger.info(f"Limpeza da sessão {session_id} concluída")
            
        except Exception as e:
            logger.error(f"Erro na limpeza da sessão {session_id}: {str(e)}")
    
    def _is_valid_pdf_file(self, filename: str) -> bool:
        """Verifica se o arquivo é um PDF válido pelo nome."""
        return (
            filename.lower().endswith('.pdf') and
            not filename.startswith('.') and
            not filename.startswith('__MACOSX')
        )
    
    def _validate_pdf_file(self, pdf_path: str) -> bool:
        """Valida se o arquivo PDF não está corrompido."""
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count > 0
        except Exception:
            return False
    
    def _is_valid_name(self, name: str) -> bool:
        """
        Valida se o texto extraído é realmente um nome de pessoa.
        
        Args:
            name: Texto para validação
            
        Returns:
            True se for um nome válido
        """
        if not name or len(name.strip()) < 3:
            return False
        
        # Remover espaços extras
        name = ' '.join(name.split())
        
        # Verificar se tem pelo menos 2 palavras (nome e sobrenome)
        words = name.split()
        if len(words) < 2:
            return False
        
        # Verificar se não contém números ou caracteres especiais demais
        if re.search(r'[0-9@#$%^&*()_+=\[\]{}|;\':".,<>?/\\]', name):
            return False
        
        # Verificar se não são palavras comuns que aparecem em diplomas
        invalid_words = {
            'diploma', 'certificado', 'curso', 'graduação', 'bacharelado',
            'licenciatura', 'universidade', 'faculdade', 'instituto',
            'mestrado', 'doutorado', 'especialização', 'data', 'ano',
            'degree', 'certificate', 'university', 'college', 'bachelor',
            'master', 'doctor', 'year', 'date'
        }
        
        name_lower = name.lower()
        if any(word in name_lower for word in invalid_words):
            return False
        
        # Verificar comprimento razoável
        if len(name) > 100:
            return False
        
        return True
