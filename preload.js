const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  openUrl: (url) => ipcRenderer.invoke('open-url', url),
  showSaveDialog: () => ipcRenderer.invoke('show-save-dialog'),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content)
})