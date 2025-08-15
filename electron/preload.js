const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    showSaveDialog: () => ipcRenderer.invoke('show-save-dialog'),
    
    // Platform information
    platform: process.platform,
    isElectron: true
});

// Desktop-specific features
contextBridge.exposeInMainWorld('desktop', {
    // File system operations
    saveFile: async (filename, content) => {
        const result = await ipcRenderer.invoke('show-save-dialog');
        if (!result.canceled) {
            return result.filePath;
        }
        return null;
    },
    
    // System notifications
    notify: (title, body) => {
        new Notification(title, { body });
    }
});