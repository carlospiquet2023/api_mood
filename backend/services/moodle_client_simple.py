"""
Cliente Moodle Simplificado e Robusto

Focado na integração via API Web Services para máxima compatibilidade
e facilidade de configuração.

Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import time

from config.settings import Config

logger = logging.getLogger(__name__)


class MoodleClient:
    """Cliente principal para integração com Moodle via Web Services API."""
    
    def __init__(self, url: str = None, token: str = None):
        """
        Inicializa o cliente Moodle.
        
        Args:
            url: URL do Moodle (usa Config.MOODLE_URL se não especificado)
            token: Token de Web Service (usa Config.MOODLE_API_TOKEN se não especificado)
        """
        self.url = url or Config.MOODLE_URL
        self.token = token or Config.MOODLE_API_TOKEN
        
        if not self.url.endswith('/'):
            self.url += '/'
        
        self.base_url = urljoin(self.url, 'webservice/rest/server.php')
        self.session = requests.Session()
        self.session.timeout = 30
        
        logger.info(f"MoodleClient inicializado para: {self.url}")
    
    def _make_request(self, function: str, **params) -> Dict[str, Any]:
        """
        Faz requisição para API do Moodle.
        
        Args:
            function: Nome da função Moodle a chamar
            **params: Parâmetros da função
            
        Returns:
            Resposta da API
            
        Raises:
            Exception: Em caso de erro na requisição
        """
        data = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json',
            **params
        }
        
        try:
            logger.debug(f"Chamando função Moodle: {function}")
            response = self.session.post(self.base_url, data=data, verify=True)
            response.raise_for_status()
            
            result = response.json()
            
            # Verificar se há erro retornado pelo Moodle
            if isinstance(result, dict) and 'exception' in result:
                error_msg = result.get('message', 'Erro desconhecido')
                raise Exception(f"Erro Moodle: {error_msg}")
            
            logger.debug(f"Função {function} executada com sucesso")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {function}: {str(e)}")
            raise Exception(f"Erro de conexão com Moodle: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta JSON: {str(e)}")
            raise Exception("Resposta inválida do Moodle")
    
    def search_users(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca usuários por nome no Moodle.
        
        Args:
            search_term: Termo de busca (nome do estudante)
            limit: Limite máximo de resultados
            
        Returns:
            Lista de usuários encontrados
        """
        try:
            # Usar core_user_get_users com critério de busca
            result = self._make_request(
                'core_user_get_users',
                criteria=[{
                    'key': 'firstname,lastname',
                    'value': search_term
                }]
            )
            
            users = result.get('users', [])
            
            # Processar e filtrar usuários
            processed_users = []
            for user in users[:limit]:
                # Filtrar apenas usuários ativos
                if user.get('deleted', False) or user.get('suspended', False):
                    continue
                
                processed_user = {
                    'id': user.get('id'),
                    'firstname': user.get('firstname', ''),
                    'lastname': user.get('lastname', ''),
                    'fullname': f"{user.get('firstname', '')} {user.get('lastname', '')}".strip(),
                    'email': user.get('email', ''),
                    'username': user.get('username', ''),
                    'profile_image': user.get('profileimageurl', ''),
                    'last_access': user.get('lastaccess', 0)
                }
                processed_users.append(processed_user)
            
            logger.info(f"Encontrados {len(processed_users)} usuários ativos para '{search_term}'")
            return processed_users
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuários: {str(e)}")
            return []
    
    def get_user_courses(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtém cursos de um usuário específico.
        
        Args:
            user_id: ID do usuário no Moodle
            
        Returns:
            Lista de cursos do usuário
        """
        try:
            result = self._make_request(
                'core_enrol_get_users_courses',
                userid=user_id
            )
            
            courses = []
            for course in result:
                course_data = {
                    'id': course.get('id'),
                    'fullname': course.get('fullname', ''),
                    'shortname': course.get('shortname', ''),
                    'category': course.get('categoryname', ''),
                    'startdate': course.get('startdate'),
                    'enddate': course.get('enddate'),
                    'enrolled': True,
                    'visible': course.get('visible', True)
                }
                courses.append(course_data)
            
            logger.info(f"Encontrados {len(courses)} cursos para usuário {user_id}")
            return courses
            
        except Exception as e:
            logger.error(f"Erro ao obter cursos do usuário {user_id}: {str(e)}")
            return []
    
    def get_course_completion_status(self, course_id: int, user_id: int) -> Dict[str, Any]:
        """
        Verifica status de conclusão de um curso para um usuário.
        
        Args:
            course_id: ID do curso
            user_id: ID do usuário
            
        Returns:
            Status de conclusão com dados formatados
        """
        try:
            result = self._make_request(
                'core_completion_get_course_completion_status',
                courseid=course_id,
                userid=user_id
            )
            
            completion_status = result.get('completionstatus', {})
            timecompleted = completion_status.get('timecompleted')
            
            return {
                'completed': bool(completion_status.get('completed', False)),
                'timecompleted': timecompleted,
                'completion_date': self._format_timestamp(timecompleted) if timecompleted else None,
                'completion_date_formatted': self._format_date(timecompleted) if timecompleted else None,
                'progress_percentage': completion_status.get('progresspercentage', 0)
            }
            
        except Exception as e:
            logger.warning(f"Erro ao verificar conclusão curso {course_id} usuário {user_id}: {str(e)}")
            return {
                'completed': False,
                'timecompleted': None,
                'completion_date': None,
                'completion_date_formatted': None,
                'progress_percentage': 0
            }
    
    def get_student_data(self, student_name: str) -> Dict[str, Any]:
        """
        Método principal - obtém dados completos do estudante incluindo cursos e conclusões.
        
        Args:
            student_name: Nome do estudante para buscar
            
        Returns:
            Dados completos do estudante com cursos e conclusões
        """
        try:
            # 1. Buscar usuários
            users = self.search_users(student_name)
            
            if not users:
                return {
                    'success': False,
                    'found': False,
                    'message': f'Nenhum estudante encontrado com o nome: {student_name}',
                    'students': [],
                    'search_term': student_name
                }
            
            # 2. Para cada usuário, enriquecer com dados de cursos
            enriched_students = []
            for user in users:
                try:
                    # Obter cursos do usuário
                    user_courses = self.get_user_courses(user['id'])
                    
                    # Verificar conclusões para cada curso
                    completed_courses = []
                    in_progress_courses = []
                    
                    for course in user_courses:
                        completion = self.get_course_completion_status(course['id'], user['id'])
                        course.update(completion)
                        
                        if completion['completed']:
                            completed_courses.append(course)
                        else:
                            in_progress_courses.append(course)
                    
                    # Dados enriquecidos do usuário
                    enriched_user = {
                        **user,
                        'total_courses': len(user_courses),
                        'completed_courses': completed_courses,
                        'in_progress_courses': in_progress_courses,
                        'completion_count': len(completed_courses),
                        'completion_rate': len(completed_courses) / len(user_courses) * 100 if user_courses else 0
                    }
                    
                    enriched_students.append(enriched_user)
                    
                except Exception as e:
                    logger.error(f"Erro ao enriquecer dados do usuário {user['id']}: {str(e)}")
                    # Adicionar usuário mesmo com erro, mas com dados básicos
                    enriched_students.append({
                        **user,
                        'total_courses': 0,
                        'completed_courses': [],
                        'in_progress_courses': [],
                        'completion_count': 0,
                        'completion_rate': 0,
                        'error': str(e)
                    })
            
            logger.info(f"Dados completos obtidos para {len(enriched_students)} estudantes")
            
            return {
                'success': True,
                'found': True,
                'message': f'Encontrados {len(enriched_students)} estudantes com dados completos',
                'students': enriched_students,
                'search_term': student_name,
                'total_found': len(enriched_students)
            }
            
        except Exception as e:
            logger.error(f"Erro geral ao obter dados do estudante '{student_name}': {str(e)}")
            return {
                'success': False,
                'found': False,
                'message': f'Erro interno ao buscar dados: {str(e)}',
                'students': [],
                'search_term': student_name,
                'error': str(e)
            }
    
    def verify_diploma_data(self, student_id: int, course_id: int) -> Dict[str, Any]:
        """
        Verifica dados específicos para validação de diploma.
        
        Args:
            student_id: ID do estudante
            course_id: ID do curso
            
        Returns:
            Dados de verificação do diploma
        """
        try:
            # Buscar dados do usuário
            user_result = self._make_request(
                'core_user_get_users_by_field',
                field='id',
                values=[student_id]
            )
            
            if not user_result:
                return {'valid': False, 'error': 'Estudante não encontrado'}
            
            user = user_result[0]
            
            # Verificar conclusão do curso
            completion = self.get_course_completion_status(course_id, student_id)
            
            if not completion['completed']:
                return {'valid': False, 'error': 'Curso não foi concluído pelo estudante'}
            
            # Buscar dados do curso
            course_result = self._make_request(
                'core_course_get_courses',
                options={'ids': [course_id]}
            )
            
            course_name = 'Curso não encontrado'
            if course_result and 'courses' in course_result:
                course_name = course_result['courses'][0].get('fullname', course_name)
            
            return {
                'valid': True,
                'student_name': f"{user.get('firstname', '')} {user.get('lastname', '')}".strip(),
                'course_name': course_name,
                'completion_date': completion['completion_date_formatted'],
                'verification_date': self._format_date(int(time.time()))
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação de diploma: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conectividade com o Moodle e retorna informações do site.
        
        Returns:
            Status da conexão e informações do site
        """
        try:
            result = self._make_request('core_webservice_get_site_info')
            
            return {
                'connected': True,
                'site_name': result.get('sitename', 'Desconhecido'),
                'site_url': result.get('siteurl', ''),
                'moodle_version': result.get('release', 'Desconhecida'),
                'functions_count': len(result.get('functions', [])),
                'user_id': result.get('userid', 0),
                'username': result.get('username', ''),
                'mobile_service': 'moodle_mobile_app' in [f.get('name', '') for f in result.get('functions', [])]
            }
            
        except Exception as e:
            logger.error(f"Teste de conexão falhou: {str(e)}")
            return {
                'connected': False,
                'error': str(e)
            }
    
    def get_site_info(self) -> Dict[str, Any]:
        """Alias para test_connection para compatibilidade."""
        return self.test_connection()
    
    @staticmethod
    def _format_timestamp(timestamp: Optional[int]) -> Optional[str]:
        """
        Formata timestamp Unix para string ISO.
        
        Args:
            timestamp: Timestamp Unix
            
        Returns:
            Data/hora formatada ou None
        """
        if timestamp and timestamp > 0:
            try:
                from datetime import datetime
                return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, OSError):
                return None
        return None
    
    @staticmethod
    def _format_date(timestamp: Optional[int]) -> Optional[str]:
        """
        Formata timestamp Unix para data legível.
        
        Args:
            timestamp: Timestamp Unix
            
        Returns:
            Data formatada ou None
        """
        if timestamp and timestamp > 0:
            try:
                from datetime import datetime
                return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y')
            except (ValueError, OSError):
                return None
        return None


# Factory function para facilitar uso
def create_moodle_client(url: str = None, token: str = None) -> MoodleClient:
    """
    Cria instância do cliente Moodle.
    
    Args:
        url: URL do Moodle (opcional)
        token: Token de acesso (opcional)
        
    Returns:
        Instância configurada do MoodleClient
    """
    return MoodleClient(url, token)
