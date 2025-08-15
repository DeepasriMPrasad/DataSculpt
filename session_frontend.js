/**
 * Frontend Session Management for CrawlOps Studio
 * Provides UI integration for session token and cookie management
 */

class SessionManager {
    constructor(apiBaseUrl = '/api/sessions') {
        this.apiBase = apiBaseUrl;
    }

    /**
     * Save session data for a domain
     */
    async saveSession(domain, cookies, options = {}) {
        const payload = {
            domain,
            cookies,
            session_name: options.sessionName,
            tokens: options.tokens,
            user_agent: navigator.userAgent,
            expires_in_days: options.expiresInDays || 30,
            notes: options.notes
        };

        const response = await fetch(`${this.apiBase}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to save session');
        }

        return data;
    }

    /**
     * Load session data for a domain
     */
    async loadSession(domain, sessionName = null) {
        const url = new URL(`${this.apiBase}/load/${encodeURIComponent(domain)}`, window.location.origin);
        if (sessionName) {
            url.searchParams.set('session_name', sessionName);
        }

        const response = await fetch(url);
        
        if (response.status === 404) {
            return null; // No session found
        }

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to load session');
        }

        return data;
    }

    /**
     * List all stored sessions
     */
    async listSessions(domain = null, activeOnly = true) {
        const url = new URL(`${this.apiBase}/list`, window.location.origin);
        if (domain) url.searchParams.set('domain', domain);
        if (!activeOnly) url.searchParams.set('active_only', 'false');

        const response = await fetch(url);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to list sessions');
        }

        return data;
    }

    /**
     * Delete a specific session
     */
    async deleteSession(options = {}) {
        const url = new URL(`${this.apiBase}/delete`, window.location.origin);
        
        if (options.sessionId) url.searchParams.set('session_id', options.sessionId);
        if (options.domain) url.searchParams.set('domain', options.domain);
        if (options.sessionName) url.searchParams.set('session_name', options.sessionName);

        const response = await fetch(url, { method: 'DELETE' });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to delete session');
        }

        return data;
    }

    /**
     * Clear multiple sessions
     */
    async clearSessions(domain = null, expiredOnly = false) {
        const url = new URL(`${this.apiBase}/clear`, window.location.origin);
        if (domain) url.searchParams.set('domain', domain);
        if (expiredOnly) url.searchParams.set('expired_only', 'true');

        const response = await fetch(url, { method: 'DELETE' });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to clear sessions');
        }

        return data;
    }

    /**
     * Get all domains with stored sessions
     */
    async getDomains() {
        const response = await fetch(`${this.apiBase}/domains`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to get domains');
        }

        return data.domains;
    }

    /**
     * Log session usage for analytics
     */
    async logUsage(sessionId, url, success, errorMessage = null) {
        const payload = {
            session_id: sessionId,
            url,
            success,
            error_message: errorMessage
        };

        const response = await fetch(`${this.apiBase}/log-usage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to log usage');
        }
    }

    /**
     * Create session management UI
     */
    createSessionUI() {
        return `
            <div class="session-manager">
                <h3 class="text-lg font-semibold mb-4">Session Management</h3>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Session List -->
                    <div class="bg-white p-4 rounded-lg shadow">
                        <h4 class="font-medium mb-3">Stored Sessions</h4>
                        <div id="session-list" class="space-y-2">
                            <!-- Sessions will be populated here -->
                        </div>
                        <button onclick="sessionManager.refreshSessions()" 
                                class="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                            Refresh Sessions
                        </button>
                    </div>

                    <!-- Session Actions -->
                    <div class="bg-white p-4 rounded-lg shadow">
                        <h4 class="font-medium mb-3">Session Actions</h4>
                        
                        <div class="space-y-3">
                            <div>
                                <label class="block text-sm font-medium mb-1">Domain Filter:</label>
                                <select id="domain-filter" class="w-full p-2 border rounded">
                                    <option value="">All Domains</option>
                                </select>
                            </div>

                            <div class="flex gap-2">
                                <button onclick="sessionManager.clearExpiredSessions()" 
                                        class="px-3 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 text-sm">
                                    Clear Expired
                                </button>
                                <button onclick="sessionManager.clearAllSessions()" 
                                        class="px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm">
                                    Clear All
                                </button>
                            </div>

                            <div class="mt-4 pt-4 border-t">
                                <h5 class="font-medium mb-2">Session Notes</h5>
                                <textarea id="session-notes" placeholder="Add notes for saved sessions..." 
                                         class="w-full p-2 border rounded h-20"></textarea>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Refresh the session list in the UI
     */
    async refreshSessions() {
        try {
            const sessions = await this.listSessions();
            const domains = await this.getDomains();
            
            this.updateSessionList(sessions);
            this.updateDomainFilter(domains);
        } catch (error) {
            console.error('Failed to refresh sessions:', error);
            this.showError('Failed to refresh sessions');
        }
    }

    /**
     * Update session list in UI
     */
    updateSessionList(sessions) {
        const listElement = document.getElementById('session-list');
        if (!listElement) return;

        if (sessions.length === 0) {
            listElement.innerHTML = '<p class="text-gray-500 text-sm">No sessions stored</p>';
            return;
        }

        listElement.innerHTML = sessions.map(session => `
            <div class="session-item flex justify-between items-center p-2 bg-gray-50 rounded">
                <div class="flex-1">
                    <div class="font-medium">${session.domain}</div>
                    <div class="text-sm text-gray-600">
                        ${session.session_name || 'Default Session'} • 
                        Created: ${new Date(session.created_at).toLocaleDateString()}
                    </div>
                    ${session.notes ? `<div class="text-xs text-gray-500">${session.notes}</div>` : ''}
                </div>
                <div class="flex gap-1">
                    <button onclick="sessionManager.deleteSession({sessionId: ${session.id}})" 
                            class="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    /**
     * Update domain filter dropdown
     */
    updateDomainFilter(domains) {
        const filterElement = document.getElementById('domain-filter');
        if (!filterElement) return;

        const currentValue = filterElement.value;
        filterElement.innerHTML = '<option value="">All Domains</option>';
        
        domains.forEach(domain => {
            const option = document.createElement('option');
            option.value = domain;
            option.textContent = domain;
            filterElement.appendChild(option);
        });

        filterElement.value = currentValue;
    }

    /**
     * Clear expired sessions
     */
    async clearExpiredSessions() {
        try {
            const result = await this.clearSessions(null, true);
            this.showSuccess(result.message);
            await this.refreshSessions();
        } catch (error) {
            this.showError(error.message);
        }
    }

    /**
     * Clear all sessions with confirmation
     */
    async clearAllSessions() {
        if (!confirm('Are you sure you want to delete all sessions? This cannot be undone.')) {
            return;
        }

        try {
            const domain = document.getElementById('domain-filter')?.value || null;
            const result = await this.clearSessions(domain);
            this.showSuccess(result.message);
            await this.refreshSessions();
        } catch (error) {
            this.showError(error.message);
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        // You can implement your own notification system here
        console.log('Success:', message);
        alert(message); // Simple fallback
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error('Error:', message);
        alert('Error: ' + message); // Simple fallback
    }
}

// Global instance
window.sessionManager = new SessionManager();