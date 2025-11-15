"""
Session and conversation context management
"""

import time
from collections import deque
from typing import Dict, List, Optional
from threading import Lock

import logging
from config import config

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversation sessions and context"""
    
    def __init__(self):
        """Initialize session manager"""
        self._sessions: Dict[str, Dict] = {}
        self._lock = Lock()
        self._max_history = config.get('session.max_history', 10)
        self._ttl = config.get('session.ttl_seconds', 3600)
        self._enabled = config.get('session.enabled', True)
    
    def get_session(self, session_id: Optional[str]) -> Optional[Dict]:
        """
        Get session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        if not self._enabled or not session_id:
            return None
        
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                # Check TTL
                if time.time() - session.get('created_at', 0) > self._ttl:
                    del self._sessions[session_id]
                    return None
                return session
            return None
    
    def create_session(self, session_id: str) -> Dict:
        """
        Create a new session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data
        """
        if not self._enabled:
            return {}
        
        with self._lock:
            session = {
                'session_id': session_id,
                'created_at': time.time(),
                'last_activity': time.time(),
                'history': deque(maxlen=self._max_history),
                'context': {}
            }
            self._sessions[session_id] = session
            return session
    
    def get_or_create_session(self, session_id: Optional[str]) -> Optional[Dict]:
        """
        Get existing session or create new one
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if session_id is None
        """
        if not session_id:
            return None
        
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        else:
            # Update last activity
            with self._lock:
                session['last_activity'] = time.time()
        
        return session
    
    def add_to_history(self, session_id: str, intent: str, text: str, entities: Dict):
        """
        Add interaction to session history
        
        Args:
            session_id: Session identifier
            intent: Detected intent
            text: Input text
            entities: Extracted entities
        """
        if not self._enabled or not session_id:
            return
        
        session = self.get_or_create_session(session_id)
        if session:
            with self._lock:
                session['history'].append({
                    'timestamp': time.time(),
                    'intent': intent,
                    'text': text[:100],  # Truncate for storage
                    'entities': entities
                })
                session['last_activity'] = time.time()
    
    def get_context(self, session_id: Optional[str]) -> Dict:
        """
        Get conversation context for better parsing
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary
        """
        if not self._enabled or not session_id:
            return {}
        
        session = self.get_session(session_id)
        if not session:
            return {}
        
        # Build context from history
        history = list(session['history'])
        context = {
            'previous_intents': [h['intent'] for h in history[-3:]],  # Last 3 intents
            'last_intent': history[-1]['intent'] if history else None,
            'interaction_count': len(history),
            'session_context': session.get('context', {})
        }
        
        return context
    
    def cleanup_expired(self):
        """Remove expired sessions (call periodically)"""
        if not self._enabled:
            return
        
        current_time = time.time()
        with self._lock:
            expired = [
                sid for sid, session in self._sessions.items()
                if current_time - session.get('created_at', 0) > self._ttl
            ]
            for sid in expired:
                del self._sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global session manager instance
session_manager = SessionManager()

