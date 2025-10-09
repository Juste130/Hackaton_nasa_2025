"""
Session Management for AI Services
Stores conversation history in SQLite with session IDs
"""
import sqlite3
import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionManager:
    """Manage conversation sessions with persistent storage"""
    
    def __init__(self, db_path: str = "sessions.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    service_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_messages 
                ON messages(session_id, timestamp)
            """)
            
            conn.commit()
    
    def create_session(
        self, 
        service_type: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create new session
        
        Args:
            service_type: 'summarizer' | 'rag_assistant' | 'generic_rag'
            metadata: Optional session metadata
        
        Returns:
            session_id: UUID string
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions (session_id, service_type, created_at, last_accessed, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                service_type,
                now,
                now,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
        
        logger.info(f" Created session: {session_id} ({service_type})")
        return session_id
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        Add message to session
        
        Args:
            session_id: Session UUID
            role: 'user' | 'assistant'
            content: Message content
            metadata: Optional metadata (citations, confidence, etc.)
        """
        now = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Add message
            conn.execute("""
                INSERT INTO messages (session_id, role, content, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                role,
                content,
                json.dumps(metadata) if metadata else None,
                now
            ))
            
            # Update last_accessed
            conn.execute("""
                UPDATE sessions 
                SET last_accessed = ?
                WHERE session_id = ?
            """, (now, session_id))
            
            conn.commit()
    
    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get conversation history for session
        
        Returns:
            List of messages with role, content, metadata, timestamp
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT role, content, metadata, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query, (session_id,))
            
            messages = []
            for row in cursor:
                message = {
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['timestamp']
                }
                
                if row['metadata']:
                    message['metadata'] = json.loads(row['metadata'])
                
                messages.append(message)
            
            return messages
    
    def get_or_create_session(
        self, 
        session_id: str, 
        service_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Get existing session or create new one if it doesn't exist
        
        Args:
            session_id: Session UUID to look for
            service_type: Service type if creating new session
            metadata: Optional metadata for new session
        
        Returns:
            Session info dictionary with session_id, service_type, etc.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Try to get existing session
            cursor = conn.execute("""
                SELECT service_type, created_at, last_accessed, metadata
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Session exists, update last_accessed and return info
                now = datetime.utcnow().isoformat()
                conn.execute("""
                    UPDATE sessions 
                    SET last_accessed = ?
                    WHERE session_id = ?
                """, (now, session_id))
                conn.commit()
                
                info = {
                    'session_id': session_id,
                    'service_type': row['service_type'],
                    'created_at': row['created_at'],
                    'last_accessed': now,
                    'existed': True
                }
                
                if row['metadata']:
                    info['metadata'] = json.loads(row['metadata'])
                
                logger.info(f"📋 Found existing session: {session_id} ({row['service_type']})")
                return info
            
            else:
                # Session doesn't exist, create new one
                now = datetime.utcnow().isoformat()
                
                conn.execute("""
                    INSERT INTO sessions (session_id, service_type, created_at, last_accessed, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    service_type,
                    now,
                    now,
                    json.dumps(metadata) if metadata else None
                ))
                conn.commit()
                
                info = {
                    'session_id': session_id,
                    'service_type': service_type,
                    'created_at': now,
                    'last_accessed': now,
                    'existed': False
                }
                
                if metadata:
                    info['metadata'] = metadata
                
                logger.info(f"✨ Created new session: {session_id} ({service_type})")
                return info
            

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session info by session_id
        
        Args:
            session_id: Session UUID
            
        Returns:
            Session info dictionary or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT service_type, created_at, last_accessed, metadata
                FROM sessions
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            
            if row:
                info = {
                    'session_id': session_id,
                    'service_type': row['service_type'],
                    'created_at': row['created_at'],
                    'last_accessed': row['last_accessed']
                }
                
                if row['metadata']:
                    info['metadata'] = json.loads(row['metadata'])
                
                return info
            
            return None

    def list_sessions(
        self,
        service_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List all sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if service_type:
                query = """
                    SELECT session_id, service_type, created_at, last_accessed
                    FROM sessions
                    WHERE service_type = ?
                    ORDER BY last_accessed DESC
                    LIMIT ?
                """
                cursor = conn.execute(query, (service_type, limit))
            else:
                query = """
                    SELECT session_id, service_type, created_at, last_accessed
                    FROM sessions
                    ORDER BY last_accessed DESC
                    LIMIT ?
                """
                cursor = conn.execute(query, (limit,))
            
            sessions = []
            for row in cursor:
                sessions.append({
                    'session_id': row['session_id'],
                    'service_type': row['service_type'],
                    'created_at': row['created_at'],
                    'last_accessed': row['last_accessed']
                })
            
            return sessions
    
    def delete_session(self, session_id: str):
        """Delete session and all messages"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        
        logger.info(f" Deleted session: {session_id}")
    
    def clear_old_sessions(self, days: int = 30):
        """Delete sessions older than N days"""
        cutoff = datetime.utcnow().replace(day=datetime.utcnow().day - days).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Get sessions to delete
            cursor = conn.execute("""
                SELECT session_id FROM sessions
                WHERE last_accessed < ?
            """, (cutoff,))
            
            session_ids = [row[0] for row in cursor]
            
            # Delete messages and sessions
            conn.execute("""
                DELETE FROM messages 
                WHERE session_id IN (
                    SELECT session_id FROM sessions WHERE last_accessed < ?
                )
            """, (cutoff,))
            
            conn.execute("DELETE FROM sessions WHERE last_accessed < ?", (cutoff,))
            conn.commit()
        
        logger.info(f" Cleared {len(session_ids)} old sessions")
        return len(session_ids)