# main idea behind "Session Manager":
    # To create unique sessions for each browser tab
    # Track processes associated with each session
    # Handle session cleanup and expiration
    # MAINN: Prevent conflicts between multiple tabs

from flask import session
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import logging

class SessionManager:
    # manage user sessions and their associated processes
    
    def __init__(self):
        self._sessions: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def create_session(self) -> str:
        # to create a new session
        session_id = str(uuid.uuid4())
        
        with self._lock:
            self._sessions[session_id] = {
                'created_at': datetime.now(),
                'last_active': datetime.now(),
                'processes': []
            }
        
        return session_id
    
    def update_session_activity(self, session_id: str):
        # to update last activity time for a session
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['last_active'] = datetime.now()
    
    def add_process_to_session(self, session_id: str, process_key: str):
        # to associate a process with a session
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['processes'].append(process_key)
    
    def remove_process_from_session(self, session_id: str, process_key: str):
        # to remove a process from a session
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]['processes'].remove(process_key)
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        # to clean up old inactive sessions
        current_time = datetime.now()
        
        with self._lock:
            to_remove = []
            for session_id, session_data in self._sessions.items():
                age = (current_time - session_data['last_active']).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(session_id)
            
            for session_id in to_remove:
                del self._sessions[session_id]
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        # Get information about a specific session
        with self._lock:
            return self._sessions.get(session_id)

# Creating global session manager instance
session_manager = SessionManager()