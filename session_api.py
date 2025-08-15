"""
Session Management API Endpoints for CrawlOps Studio
Provides REST API for session token and cookie management
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from session_manager import session_manager
import sqlite3

# Create router for session endpoints
router = APIRouter(prefix="/api/sessions", tags=["Session Management"])


# Pydantic models for API requests/responses
class SessionSaveRequest(BaseModel):
    domain: str = Field(..., description="Domain for the session")
    cookies: Dict[str, Any] = Field(..., description="Session cookies")
    session_name: Optional[str] = Field(None, description="Custom session name")
    tokens: Optional[Dict[str, str]] = Field(None, description="Authentication tokens")
    user_agent: Optional[str] = Field(None, description="User agent string")
    expires_in_days: int = Field(30, description="Session expiration in days")
    notes: Optional[str] = Field(None, description="Notes about this session")


class SessionResponse(BaseModel):
    id: int
    domain: str
    session_name: Optional[str]
    created_at: str
    updated_at: str
    expires_at: Optional[str]
    is_active: bool
    notes: Optional[str]


class SessionDetailsResponse(BaseModel):
    id: int
    domain: str
    session_name: Optional[str]
    cookies: Dict[str, Any]
    tokens: Dict[str, str]
    user_agent: Optional[str]
    created_at: str
    expires_at: Optional[str]
    notes: Optional[str]
    stats: Optional[Dict[str, Any]] = None


class SessionUsageRequest(BaseModel):
    session_id: int
    url: str
    success: bool
    error_message: Optional[str] = None


@router.post("/save", response_model=Dict[str, Any])
async def save_session(request: SessionSaveRequest):
    """Save session cookies and tokens for a domain."""
    try:
        session_id = session_manager.save_session(
            domain=request.domain,
            cookies=request.cookies,
            session_name=request.session_name,
            tokens=request.tokens,
            user_agent=request.user_agent,
            expires_in_days=request.expires_in_days,
            notes=request.notes
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": f"Session saved for {request.domain}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")


@router.get("/load/{domain}", response_model=SessionDetailsResponse)
async def load_session(domain: str, session_name: Optional[str] = None):
    """Load session data for a domain."""
    try:
        session_data = session_manager.load_session(domain, session_name)
        
        if not session_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No active session found for domain: {domain}"
            )
        
        # Add usage statistics
        session_data['stats'] = session_manager.get_session_stats(session_data['id'])
        
        return SessionDetailsResponse(**session_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load session: {str(e)}")


@router.get("/list", response_model=List[SessionResponse])
async def list_sessions(domain: Optional[str] = None, active_only: bool = True):
    """List all stored sessions."""
    try:
        sessions = session_manager.list_sessions(domain, active_only)
        return [SessionResponse(**session) for session in sessions]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.delete("/delete")
async def delete_session(
    session_id: Optional[int] = None, 
    domain: Optional[str] = None, 
    session_name: Optional[str] = None
):
    """Delete a specific session."""
    try:
        if not any([session_id, domain]):
            raise HTTPException(
                status_code=400, 
                detail="Must provide session_id, domain, or both domain and session_name"
            )
        
        deleted = session_manager.delete_session(session_id, domain, session_name)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "message": "Session deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.delete("/clear")
async def clear_sessions(domain: Optional[str] = None, expired_only: bool = False):
    """Clear sessions (all, by domain, or expired only)."""
    try:
        if expired_only:
            deleted_count = session_manager.clear_expired_sessions()
            message = f"Cleared {deleted_count} expired sessions"
        else:
            deleted_count = session_manager.clear_all_sessions(domain)
            if domain:
                message = f"Cleared {deleted_count} sessions for domain: {domain}"
            else:
                message = f"Cleared all {deleted_count} sessions"
        
        return {
            "success": True, 
            "deleted_count": deleted_count,
            "message": message
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear sessions: {str(e)}")


@router.patch("/deactivate/{session_id}")
async def deactivate_session(session_id: int):
    """Deactivate a session without deleting it."""
    try:
        updated = session_manager.deactivate_session(session_id)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"success": True, "message": "Session deactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate session: {str(e)}")


@router.post("/log-usage")
async def log_session_usage(request: SessionUsageRequest):
    """Log session usage for analytics."""
    try:
        session_manager.log_session_usage(
            session_id=request.session_id,
            url=request.url,
            success=request.success,
            error_message=request.error_message
        )
        
        return {"success": True, "message": "Usage logged successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log usage: {str(e)}")


@router.get("/stats/{session_id}")
async def get_session_stats(session_id: int):
    """Get usage statistics for a session."""
    try:
        stats = session_manager.get_session_stats(session_id)
        return {"success": True, "stats": stats}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")


@router.get("/domains")
async def get_session_domains():
    """Get list of all domains with stored sessions."""
    try:
        sessions = session_manager.list_sessions(active_only=True)
        domains = list(set(session['domain'] for session in sessions))
        domains.sort()
        
        return {"success": True, "domains": domains}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get domains: {str(e)}")


@router.get("/health")
async def session_health():
    """Health check for session management."""
    try:
        # Test database connection
        sessions = session_manager.list_sessions()
        return {
            "success": True, 
            "message": "Session management is healthy",
            "total_sessions": len(sessions)
        }
    
    except Exception as e:
        return {
            "success": False, 
            "message": f"Session management unhealthy: {str(e)}"
        }