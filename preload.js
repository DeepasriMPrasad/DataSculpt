const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App control
  getVersion: () => ipcRenderer.invoke('app:getVersion'),
  quit: () => ipcRenderer.invoke('app:quit'),
  
  // File operations
  openUrl: (url) => ipcRenderer.invoke('open-url', url),
  showSaveDialog: () => ipcRenderer.invoke('show-save-dialog'),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  
  // External links
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
  
  // Window management
  minimize: () => ipcRenderer.invoke('window:minimize'),
  maximize: () => ipcRenderer.invoke('window:maximize'),
  close: () => ipcRenderer.invoke('window:close'),
  
  // File system operations
  selectDirectory: () => ipcRenderer.invoke('dialog:selectDirectory'),
  selectFiles: (options) => ipcRenderer.invoke('dialog:selectFiles', options),
  
  // Development helpers
  openDevTools: () => ipcRenderer.invoke('dev:openDevTools')
});