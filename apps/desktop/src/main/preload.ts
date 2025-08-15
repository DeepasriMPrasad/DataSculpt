import { contextBridge, ipcRenderer } from 'electron';

const electronAPI = {
  // Profile management
  getProfile: () => ipcRenderer.invoke('profile:get'),
  setProfile: (profile: string, overrides?: any) => ipcRenderer.invoke('profile:set', { profile, overrides }),

  // Authentication
  login: (url?: string) => ipcRenderer.invoke('auth:login', { url }),

  // Challenge handling
  onCaptchaDetected: (callback: (data: any) => void) => 
    ipcRenderer.on('challenge:captchaDetected', (_, data) => callback(data)),
  awaitUserAction: () => ipcRenderer.invoke('challenge:awaitUserAction'),

  // Capture operations
  captureSingleFile: (url: string) => ipcRenderer.invoke('capture:singlefile', { url }),
  capturePDF: (htmlPath: string, options?: any) => ipcRenderer.invoke('capture:pdf', { singlefileHtmlPath: htmlPath, options }),

  // Queue management
  enqueueURLs: (urls: string[], options: any) => ipcRenderer.invoke('queue:enqueue', { urls, options }),
  getQueueStatus: () => ipcRenderer.invoke('queue:status'),
  pauseItem: (url: string) => ipcRenderer.invoke('queue:pauseItem', { url }),
  resumeItem: (url: string) => ipcRenderer.invoke('queue:resumeItem', { url }),

  // Settings
  getSettings: () => ipcRenderer.invoke('settings:get'),
  setSettings: (settings: any) => ipcRenderer.invoke('settings:set', settings),

  // Network configuration
  setCertificates: (path: string) => ipcRenderer.invoke('certs:setCABundle', { path }),
  setProxy: (config: any) => ipcRenderer.invoke('network:setProxy', config),

  // Utilities
  openExternal: (url: string) => ipcRenderer.invoke('shell:openExternal', { url }),
  showSaveDialog: (options: any) => ipcRenderer.invoke('dialog:showSaveDialog', options),
  showOpenDialog: (options: any) => ipcRenderer.invoke('dialog:showOpenDialog', options),
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);

export type ElectronAPI = typeof electronAPI;
