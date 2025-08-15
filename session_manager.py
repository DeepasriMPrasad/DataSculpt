"""
Session Token and Cookie Management for CrawlOps Studio
Provides persistent storage and management of authentication sessions
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class SessionManager:
    """Manages persistent storage of session tokens and cookies."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize session manager with local storage."""
        if data_dir is None:
            data_dir = os.path.expanduser("~/.crawlops")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "sessions.db"
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database for session storage."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                session_name TEXT,
                cookies TEXT NOT NULL,
                tokens TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                notes TEXT,
                UNIQUE(domain, session_name)
            )
        ''')
        
        # Create session_usage table for tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                url TEXT,
                success BOOLEAN,
                error_message TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_session(self, domain: str, cookies: Dict[str, Any], 
                     session_name: Optional[str] = None, tokens: Optional[Dict[str, str]] = None,
                     user_agent: Optional[str] = None, expires_in_days: int = 30,
                     notes: Optional[str] = None) -> int:
        """Save session cookies and tokens for a domain."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if session_name is None:
            session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cookies_json = json.dumps(cookies)
        tokens_json = json.dumps(tokens) if tokens else None
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (domain, session_name, cookies, tokens, user_agent, updated_at, expires_at, notes)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            ''', (domain, session_name, cookies_json, tokens_json, user_agent, expires_at, notes))
            
            session_id = cursor.lastrowid or 0
            conn.commit()
            return session_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def load_session(self, domain: str, session_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load session data for a domain."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if session_name:
            cursor.execute('''
                SELECT id, cookies, tokens, user_agent, created_at, expires_at, notes
                FROM sessions 
                WHERE domain = ? AND session_name = ? AND is_active = 1 
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ''', (domain, session_name))
        else:
            # Get the most recent active session
            cursor.execute('''
                SELECT id, cookies, tokens, user_agent, created_at, expires_at, notes
                FROM sessions 
                WHERE domain = ? AND is_active = 1 
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY updated_at DESC LIMIT 1
            ''', (domain,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            session_id, cookies_json, tokens_json, user_agent, created_at, expires_at, notes = result
            return {
                'id': session_id,
                'cookies': json.loads(cookies_json),
                'tokens': json.loads(tokens_json) if tokens_json else {},
                'user_agent': user_agent,
                'created_at': created_at,
                'expires_at': expires_at,
                'notes': notes
            }
        
        return None
    
    def list_sessions(self, domain: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all stored sessions."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        query = '''
            SELECT id, domain, session_name, created_at, updated_at, expires_at, is_active, notes
            FROM sessions
        '''
        params = []
        
        conditions = []
        if domain:
            conditions.append("domain = ?")
            params.append(domain)
        
        if active_only:
            conditions.append("is_active = 1")
            conditions.append("(expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY updated_at DESC"
        
        cursor.execute(query, params)
        sessions = []
        
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'domain': row[1],
                'session_name': row[2],
                'created_at': row[3],
                'updated_at': row[4],
                'expires_at': row[5],
                'is_active': bool(row[6]),
                'notes': row[7]
            })
        
        conn.close()
        return sessions
    
    def delete_session(self, session_id: Optional[int] = None, domain: Optional[str] = None, 
                       session_name: Optional[str] = None) -> bool:
        """Delete a specific session."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if session_id:
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        elif domain and session_name:
            cursor.execute("DELETE FROM sessions WHERE domain = ? AND session_name = ?", 
                         (domain, session_name))
        elif domain:
            cursor.execute("DELETE FROM sessions WHERE domain = ?", (domain,))
        else:
            raise ValueError("Must provide session_id, or domain, or domain+session_name")
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def clear_expired_sessions(self) -> int:
        """Remove expired sessions and return count."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM sessions 
            WHERE expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP
        ''')
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def clear_all_sessions(self, domain: Optional[str] = None) -> int:
        """Clear all sessions, optionally for a specific domain."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if domain:
            cursor.execute("DELETE FROM sessions WHERE domain = ?", (domain,))
        else:
            cursor.execute("DELETE FROM sessions")
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def deactivate_session(self, session_id: int) -> bool:
        """Deactivate a session without deleting it."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session_id,))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def log_session_usage(self, session_id: int, url: str, success: bool, 
                          error_message: Optional[str] = None):
        """Log session usage for analytics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_usage (session_id, url, success, error_message)
            VALUES (?, ?, ?, ?)
        ''', (session_id, url, success, error_message))
        
        conn.commit()
        conn.close()
    
    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """Get usage statistics for a session."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total_uses, 
                   SUM(success) as successful_uses,
                   MAX(used_at) as last_used
            FROM session_usage 
            WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            total, successful, last_used = result
            return {
                'total_uses': total,
                'successful_uses': successful,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'last_used': last_used
            }
        
        return {'total_uses': 0, 'successful_uses': 0, 'success_rate': 0, 'last_used': None}


# Global session manager instance
session_manager = SessionManager()