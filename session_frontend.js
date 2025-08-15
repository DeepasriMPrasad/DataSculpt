// Session Management Frontend Integration
// This file provides session management functionality for the CrawlOps Studio frontend

class SessionManager {
    constructor() {
        this.baseUrl = window.location.origin + '/api/sessions';
    }

    async saveSession(domain, cookies, tokens = {}, notes = '') {
        try {
            const response = await fetch(`${this.baseUrl}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domain, cookies, tokens, notes })
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to save session:', error);
            return { success: false, error: error.message };
        }
    }

    async loadSession(domain) {
        try {
            const response = await fetch(`${this.baseUrl}/load/${domain}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to load session:', error);
            return null;
        }
    }

    async listSessions() {
        try {
            const response = await fetch(`${this.baseUrl}/list`);
            return await response.json();
        } catch (error) {
            console.error('Failed to list sessions:', error);
            return [];
        }
    }

    async getDomains() {
        try {
            const response = await fetch(`${this.baseUrl}/domains`);
            const data = await response.json();
            return data.domains || [];
        } catch (error) {
            console.error('Failed to get domains:', error);
            return [];
        }
    }

    async clearSessions(expiredOnly = true) {
        try {
            const response = await fetch(`${this.baseUrl}/clear${expiredOnly ? '?expired_only=true' : ''}`, {
                method: 'DELETE'
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to clear sessions:', error);
            return { success: false, error: error.message };
        }
    }

    async getHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Session service health check failed:', error);
            return { success: false };
        }
    }
}

// Make SessionManager globally available
window.SessionManager = SessionManager;