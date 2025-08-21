"""
Gerenciador de Sessões
Desenvolvido por: Carlos Antonio de Oliveira Piquet
Email: carlospiquet.projetos@gmail.com
Contato: +55 21 977434614

Este módulo gerencia sessões de usuário, armazenamento temporário
de dados e limpeza automática de recursos.
"""

import os
import json
import time
import uuid
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import atexit

from config.settings import Config

logger = logging.getLogger(__name__)


class SessionManager:
    """Gerenciador de sessões de usuário."""
    
    def __init__(self):
        """Inicializa o gerenciador de sessões."""
        self.session_timeout = Config.SESSION_TIMEOUT
        self.cleanup_interval = Config.SESSION_CLEANUP_INTERVAL
        
        # Diretório para dados de sessão
        self.sessions_dir = Path(tempfile.gettempdir()) / 'diploma_sessions'
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Lock para operações thread-safe
        self._lock = threading.Lock()
        
        # Timer para limpeza automática
        self._cleanup_timer = None
        self._start_cleanup_timer()
        
        # Registrar limpeza na saída
        atexit.register(self.cleanup_all_sessions)
        
        logger.info("SessionManager inicializado")
    
    def create_session(self) -> str:
        """
        Cria uma nova sessão.
        
        Returns:
            ID único da sessão
        """
        try:
            # Gerar ID único
            session_id = str(uuid.uuid4())
            
            # Dados iniciais da sessão
            session_data = {
                'id': session_id,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'status': 'active',
                'data': {}
            }
            
            # Salvar sessão
            self._save_session_metadata(session_id, session_data)
            
            logger.info(f"Nova sessão criada: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Erro ao criar sessão: {str(e)}", exc_info=True)
            raise
    
    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dados da sessão ou None se não encontrada/expirada
        """
        try:
            with self._lock:
                if not self._session_exists(session_id):
                    logger.warning(f"Sessão não encontrada: {session_id}")
                    return None
                
                # Verificar se não expirou
                if self._is_session_expired(session_id):
                    logger.warning(f"Sessão expirada: {session_id}")
                    self._cleanup_session_files(session_id)
                    return None
                
                # Carregar dados
                session_data = self._load_session_metadata(session_id)
                if session_data:
                    # Atualizar último acesso
                    session_data['last_accessed'] = time.time()
                    self._save_session_metadata(session_id, session_data)
                    
                    return session_data.get('data', {})
                
                return None
                
        except Exception as e:
            logger.error(f"Erro ao recuperar dados da sessão {session_id}: {str(e)}")
            return None
    
    def store_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Armazena dados na sessão.
        
        Args:
            session_id: ID da sessão
            data: Dados para armazenar
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            with self._lock:
                if not self._session_exists(session_id):
                    logger.warning(f"Tentativa de armazenar dados em sessão inexistente: {session_id}")
                    return False
                
                # Carregar sessão atual
                session_data = self._load_session_metadata(session_id)
                if not session_data:
                    return False
                
                # Verificar se não expirou
                if self._is_session_expired(session_id):
                    logger.warning(f"Tentativa de armazenar dados em sessão expirada: {session_id}")
                    self._cleanup_session_files(session_id)
                    return False
                
                # Atualizar dados
                session_data['data'].update(data)
                session_data['last_accessed'] = time.time()
                
                # Salvar
                self._save_session_metadata(session_id, session_data)
                
                logger.debug(f"Dados armazenados na sessão {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao armazenar dados na sessão {session_id}: {str(e)}")
            return False
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        Atualiza status da sessão.
        
        Args:
            session_id: ID da sessão
            status: Novo status
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            with self._lock:
                session_data = self._load_session_metadata(session_id)
                if not session_data:
                    return False
                
                session_data['status'] = status
                session_data['last_accessed'] = time.time()
                
                self._save_session_metadata(session_id, session_data)
                
                logger.debug(f"Status da sessão {session_id} atualizado para: {status}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao atualizar status da sessão {session_id}: {str(e)}")
            return False
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Remove uma sessão específica.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se removida com sucesso
        """
        try:
            with self._lock:
                self._cleanup_session_files(session_id)
                logger.info(f"Sessão removida: {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao remover sessão {session_id}: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove todas as sessões expiradas.
        
        Returns:
            Número de sessões removidas
        """
        try:
            logger.info("Iniciando limpeza de sessões expiradas")
            
            removed_count = 0
            current_time = time.time()
            
            # Listar todas as sessões
            session_files = list(self.sessions_dir.glob("session_*.json"))
            
            for session_file in session_files:
                try:
                    # Extrair ID da sessão do nome do arquivo
                    session_id = session_file.stem.replace('session_', '')
                    
                    # Verificar se expirou
                    if self._is_session_expired(session_id):
                        self._cleanup_session_files(session_id)
                        removed_count += 1
                        logger.debug(f"Sessão expirada removida: {session_id}")
                
                except Exception as e:
                    logger.error(f"Erro ao verificar sessão {session_file}: {str(e)}")
            
            logger.info(f"Limpeza concluída: {removed_count} sessões removidas")
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de sessões: {str(e)}")
            return 0
    
    def cleanup_all_sessions(self):
        """Remove todas as sessões (usado na saída da aplicação)."""
        try:
            logger.info("Removendo todas as sessões")
            
            # Parar timer de limpeza
            if self._cleanup_timer:
                self._cleanup_timer.cancel()
            
            # Remover diretório de sessões
            import shutil
            if self.sessions_dir.exists():
                shutil.rmtree(self.sessions_dir)
            
            logger.info("Todas as sessões foram removidas")
            
        except Exception as e:
            logger.error(f"Erro na limpeza geral: {str(e)}")
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de sessões ativas.
        
        Returns:
            Lista com informações das sessões ativas
        """
        try:
            active_sessions = []
            session_files = list(self.sessions_dir.glob("session_*.json"))
            
            for session_file in session_files:
                try:
                    session_id = session_file.stem.replace('session_', '')
                    
                    if not self._is_session_expired(session_id):
                        session_data = self._load_session_metadata(session_id)
                        if session_data:
                            active_sessions.append({
                                'id': session_id,
                                'created_at': session_data.get('created_at'),
                                'last_accessed': session_data.get('last_accessed'),
                                'status': session_data.get('status'),
                                'age_minutes': (time.time() - session_data.get('created_at', 0)) / 60
                            })
                
                except Exception as e:
                    logger.error(f"Erro ao processar sessão {session_file}: {str(e)}")
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Erro ao listar sessões ativas: {str(e)}")
            return []
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas das sessões.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            active_sessions = self.get_active_sessions()
            
            stats = {
                'total_active': len(active_sessions),
                'session_timeout_minutes': self.session_timeout / 60,
                'cleanup_interval_minutes': self.cleanup_interval / 60,
                'sessions_directory': str(self.sessions_dir),
            }
            
            if active_sessions:
                ages = [s['age_minutes'] for s in active_sessions]
                stats.update({
                    'oldest_session_minutes': max(ages),
                    'newest_session_minutes': min(ages),
                    'average_age_minutes': sum(ages) / len(ages)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {}
    
    def _session_exists(self, session_id: str) -> bool:
        """Verifica se sessão existe."""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        return session_file.exists()
    
    def _is_session_expired(self, session_id: str) -> bool:
        """Verifica se sessão expirou."""
        try:
            session_data = self._load_session_metadata(session_id)
            if not session_data:
                return True
            
            last_accessed = session_data.get('last_accessed', 0)
            return (time.time() - last_accessed) > self.session_timeout
            
        except Exception:
            return True
    
    def _load_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega metadados da sessão."""
        try:
            session_file = self.sessions_dir / f"session_{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Erro ao carregar sessão {session_id}: {str(e)}")
            return None
    
    def _save_session_metadata(self, session_id: str, data: Dict[str, Any]):
        """Salva metadados da sessão."""
        try:
            session_file = self.sessions_dir / f"session_{session_id}.json"
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erro ao salvar sessão {session_id}: {str(e)}")
            raise
    
    def _cleanup_session_files(self, session_id: str):
        """Remove todos os arquivos de uma sessão."""
        try:
            # Remover metadados da sessão
            session_file = self.sessions_dir / f"session_{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            # Remover arquivos temporários da sessão
            temp_dirs = [
                Path(tempfile.gettempdir()) / 'diploma_processor' / f"session_{session_id}",
                Path(tempfile.gettempdir()) / 'diploma_processor' / f"output_{session_id}",
                Path(tempfile.gettempdir()) / 'diploma_qr_codes' / f"qr_{session_id}",
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
            
            # Remover arquivos ZIP da sessão
            for zip_file in Path(tempfile.gettempdir()).glob(f"*{session_id}*.zip"):
                zip_file.unlink()
                
        except Exception as e:
            logger.error(f"Erro ao limpar arquivos da sessão {session_id}: {str(e)}")
    
    def _start_cleanup_timer(self):
        """Inicia timer para limpeza automática."""
        try:
            self._cleanup_timer = threading.Timer(
                self.cleanup_interval,
                self._cleanup_and_reschedule
            )
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar timer de limpeza: {str(e)}")
    
    def _cleanup_and_reschedule(self):
        """Executa limpeza e reagenda próxima."""
        try:
            self.cleanup_expired_sessions()
            self._start_cleanup_timer()  # Reagendar
            
        except Exception as e:
            logger.error(f"Erro no timer de limpeza: {str(e)}")
            # Tentar reagendar mesmo com erro
            try:
                self._start_cleanup_timer()
            except:
                pass
