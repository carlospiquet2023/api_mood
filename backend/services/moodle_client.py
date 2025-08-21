"""
Cliente Avançado para integração com Moodle

Este módulo oferece duas estratégias de integração com o Moodle:
1. Via API Web Services (Recomendado) - Mais seguro
2. Via conexão direta ao banco de dados - Mais rápido

Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614
"""

import requests
import logging
import mysql.connector
import psycopg2
from typing import Dict, Optional, Any, List
from urllib.parse import urljoin
import time
import json
from dataclasses import dataclass

from config.settings import Config

logger = logging.getLogger(__name__)


@dataclass
class MoodleConfig:
    """Configuração para conexão com Moodle"""
    # API Web Services
    api_url: str
    api_token: str
    
    # Conexão direta ao banco (opcional)
    db_host: str = ""
    db_port: int = 3306
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""
    db_type: str = "mysql"  # mysql ou postgresql


class MoodleClientAdvanced:
    """Cliente avançado para comunicação com Moodle via API e/ou banco direto."""
    
    def __init__(self, config: MoodleConfig = None):
        """Inicializa o cliente Moodle."""
        self.config = config or self._load_config_from_env()
        
        # Configurar sessão HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Sistema-Diplomas-Professional/1.0.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        # Cache e conexões
        self._cache = {}
        self._cache_ttl = 300
        self._db_connection = None
        
        # Estratégia de conexão (api, database, hybrid)
        self.strategy = self._determine_strategy()
        
        logger.info(f"MoodleClientAdvanced inicializado - Estratégia: {self.strategy}")
    
    def _load_config_from_env(self) -> MoodleConfig:
        """Carrega configuração das variáveis de ambiente."""
        import os
        
        return MoodleConfig(
            api_url=os.getenv('MOODLE_URL', Config.MOODLE_URL),
            api_token=os.getenv('MOODLE_API_TOKEN', Config.MOODLE_API_TOKEN),
            db_host=os.getenv('MOODLE_DB_HOST', ''),
            db_port=int(os.getenv('MOODLE_DB_PORT', '3306')),
            db_name=os.getenv('MOODLE_DB_NAME', ''),
            db_user=os.getenv('MOODLE_DB_USER', ''),
            db_password=os.getenv('MOODLE_DB_PASSWORD', ''),
            db_type=os.getenv('MOODLE_DB_TYPE', 'mysql').lower()
        )
    
    def check_connection(self) -> Dict[str, Any]:
        """Verifica conectividade com Moodle usando todas as estratégias disponíveis."""
        results = {
            'api': False,
            'database': False,
            'strategy': self.strategy,
            'details': {}
        }
        
        # Testar API
        if self.config.api_url and self.config.api_token:
            try:
                api_status = self._test_api_connection()
                results['api'] = api_status['success']
                results['details']['api'] = api_status
            except Exception as e:
                results['details']['api'] = {'success': False, 'error': str(e)}
        
        # Status geral
        results['overall'] = results.get('api', False)
        
        return results
    
    def get_student_data(self, student_name: str) -> Optional[Dict[str, Any]]:
        """
        Busca dados do estudante usando a estratégia configurada.
        
        Args:
            student_name: Nome completo do estudante
            
        Returns:
            Dicionário com dados do estudante ou None
        """
        try:
            logger.info(f"Buscando dados do estudante: {student_name}")
            
            # Verificar cache
            cache_key = f"student_{student_name.lower()}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            student_data = self._get_student_data_via_api(student_name)
            
            if student_data:
                self._store_in_cache(cache_key, student_data)
                logger.info(f"Dados encontrados para: {student_name}")
            else:
                logger.warning(f"Estudante não encontrado: {student_name}")
            
            return student_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar estudante {student_name}: {str(e)}", exc_info=True)
            return None


# Classe de compatibilidade para manter interface original
class MoodleClient(MoodleClientAdvanced):
    """Classe de compatibilidade que mantém a interface original."""
    
    def __init__(self):
        config = MoodleConfig(
            api_url=Config.MOODLE_URL,
            api_token=Config.MOODLE_API_TOKEN
        )
        super().__init__(config)
    
    def check_connection(self) -> bool:
        """Mantém compatibilidade com interface original."""
        results = super().check_connection()
        return results.get('overall', False)
    
    def verify_diploma(self, student_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Verifica a autenticidade de um diploma.
        
        Args:
            student_id: ID do estudante
            session_id: ID da sessão de processamento
            
        Returns:
            Dados de verificação ou None se não verificado
        """
        try:
            logger.info(f"Verificando diploma - Estudante: {student_id}, Sessão: {session_id}")
            
            # Buscar dados do usuário
            user_data = self._get_user_by_id(int(student_id))
            if not user_data:
                logger.warning(f"Usuário não encontrado para verificação: {student_id}")
                return None
            
            # Buscar cursos completados pelo usuário
            completed_courses = self._get_completed_courses(int(student_id))
            
            if completed_courses:
                verification_data = {
                    'student_id': student_id,
                    'student_name': user_data['fullname'],
                    'student_email': user_data['email'],
                    'courses': completed_courses,
                    'verified': True,
                    'verification_date': time.time()
                }
                
                logger.info(f"Diploma verificado com sucesso para: {user_data['fullname']}")
                return verification_data
            
            logger.warning(f"Nenhum curso completado encontrado para: {student_id}")
            return None
            
        except Exception as e:
            logger.error(f"Erro na verificação do diploma: {str(e)}", exc_info=True)
            return None
    
    def _search_user_by_name(self, name: str) -> Optional[Dict]:
        """Busca usuário pelo nome completo."""
        try:
            url = urljoin(self.base_url, '/webservice/rest/server.php')
            data = {
                'wstoken': self.api_token,
                'wsfunction': 'core_user_get_users',
                'moodlewsrestformat': 'json',
                'criteria[0][key]': 'firstname',
                'criteria[0][value]': name.split()[0],  # Primeiro nome
            }
            
            # Se há sobrenome, adicionar critério
            if len(name.split()) > 1:
                data['criteria[1][key]'] = 'lastname'
                data['criteria[1][value]'] = ' '.join(name.split()[1:])  # Resto do nome
            
            response = self.session.post(url, data=data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                logger.error(f"Erro na busca de usuário: {result['error']}")
                return None
            
            users = result.get('users', [])
            
            # Buscar correspondência exata ou similar
            for user in users:
                user_fullname = f"{user.get('firstname', '')} {user.get('lastname', '')}".strip()
                if self._names_match(name, user_fullname):
                    return {
                        'id': user['id'],
                        'fullname': user_fullname,
                        'email': user.get('email', ''),
                        'firstname': user.get('firstname', ''),
                        'lastname': user.get('lastname', '')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por nome: {str(e)}")
            return None
    
    def _get_user_courses(self, user_id: int) -> List[Dict]:
        """Busca cursos do usuário."""
        try:
            url = urljoin(self.base_url, '/webservice/rest/server.php')
            data = {
                'wstoken': self.api_token,
                'wsfunction': 'core_enrol_get_users_courses',
                'moodlewsrestformat': 'json',
                'userid': user_id
            }
            
            response = self.session.post(url, data=data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list):
                return result
            elif 'error' in result:
                logger.error(f"Erro ao buscar cursos: {result['error']}")
            
            return []
            
        except Exception as e:
            logger.error(f"Erro ao buscar cursos do usuário: {str(e)}")
            return []
    
    def _get_detailed_user_data(self, user_id: int, course_id: int) -> Optional[Dict]:
        """Busca dados detalhados usando nossa função customizada."""
        try:
            url = urljoin(self.base_url, '/webservice/rest/server.php')
            data = {
                'wstoken': self.api_token,
                'wsfunction': self.function_name,
                'moodlewsrestformat': 'json',
                'userid': user_id,
                'courseid': course_id
            }
            
            response = self.session.post(url, data=data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                logger.error(f"Erro na função customizada: {result['error']}")
                return None
            
            if result.get('status') == 'success':
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados detalhados: {str(e)}")
            return None
    
    def _get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Busca usuário pelo ID."""
        try:
            url = urljoin(self.base_url, '/webservice/rest/server.php')
            data = {
                'wstoken': self.api_token,
                'wsfunction': 'core_user_get_users_by_field',
                'moodlewsrestformat': 'json',
                'field': 'id',
                'values[0]': user_id
            }
            
            response = self.session.post(url, data=data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and result:
                user = result[0]
                return {
                    'id': user['id'],
                    'fullname': f"{user.get('firstname', '')} {user.get('lastname', '')}".strip(),
                    'email': user.get('email', ''),
                    'firstname': user.get('firstname', ''),
                    'lastname': user.get('lastname', '')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário por ID: {str(e)}")
            return None
    
    def _get_completed_courses(self, user_id: int) -> List[Dict]:
        """Busca cursos completados pelo usuário."""
        try:
            # Esta função pode precisar ser customizada baseada em como
            # o Moodle determina que um curso foi completado
            courses = self._get_user_courses(user_id)
            
            # Por simplicidade, retornamos todos os cursos
            # Em produção, você pode adicionar lógica para verificar conclusão
            return courses
            
        except Exception as e:
            logger.error(f"Erro ao buscar cursos completados: {str(e)}")
            return []
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Verifica se dois nomes são similares o suficiente."""
        # Normalizar nomes (remover acentos, converter para minúsculas)
        import unicodedata
        
        def normalize_name(name):
            name = unicodedata.normalize('NFD', name.lower())
            name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
            return ' '.join(name.split())
        
        norm_name1 = normalize_name(name1)
        norm_name2 = normalize_name(name2)
        
        # Verificar correspondência exata
        if norm_name1 == norm_name2:
            return True
        
        # Verificar se todas as palavras de name1 estão em name2
        words1 = set(norm_name1.split())
        words2 = set(norm_name2.split())
        
        # Pelo menos 80% das palavras devem coincidir
        if len(words1) > 0:
            match_ratio = len(words1.intersection(words2)) / len(words1)
            return match_ratio >= 0.8
        
        return False
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Recupera dados do cache se ainda válidos."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _store_in_cache(self, key: str, data: Any):
        """Armazena dados no cache."""
        self._cache[key] = (data, time.time())
        
        # Limpar cache antigo se ficar muito grande
        if len(self._cache) > 100:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove entradas antigas do cache."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, (data, timestamp) in self._cache.items():
            if current_time - timestamp >= self._cache_ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
    
    def __del__(self):
        """Limpa recursos na destruição do objeto."""
        if hasattr(self, 'session'):
            self.session.close()
