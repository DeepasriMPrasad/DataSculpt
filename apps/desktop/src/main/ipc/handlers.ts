import { ipcMain, dialog, shell, session } from 'electron';
import { IPC_CHANNELS } from './channels';
import * as fs from 'fs';
import * as path from 'path';
import type { URLItem, CrawlSettings, ExecutionProfile } from '../../shared/types';

class CrawlQueue {
  private items: Map<string, URLItem> = new Map();
  private settings: CrawlSettings | null = null;
  private isRunning = false;

  addItems(urls: string[], options: any) {
    let enqueued = 0;
    urls.forEach(url => {
      if (!this.items.has(url)) {
        const item: URLItem = {
          url,
          depth: options.depth || 0,
          status: 'queued',
          formats: options.formats || {},
          attempts: 0,
          profile: options.profile || 'standard'
        };
        this.items.set(url, item);
        enqueued++;
      }
    });
    return enqueued;
  }

  getItems(): URLItem[] {
    return Array.from(this.items.values());
  }

  getStats() {
    const items = this.getItems();
    return {
      running: items.filter(i => i.status === 'running').length,
      waiting: items.filter(i => i.status === 'waiting_captcha' || i.status === 'waiting_user').length,
      done: items.filter(i => i.status === 'done').length,
      failed: items.filter(i => i.status === 'failed').length,
      total: items.length
    };
  }

  pauseItem(url: string) {
    const item = this.items.get(url);
    if (item && item.status === 'running') {
      item.status = 'waiting_user';
      return true;
    }
    return false;
  }

  resumeItem(url: string) {
    const item = this.items.get(url);
    if (item && item.status === 'waiting_user') {
      item.status = 'queued';
      return true;
    }
    return false;
  }
}

const queue = new CrawlQueue();
const profiles: Record<ExecutionProfile, any> = {
  standard: { concurrency: 3, delay: 1000, respectRobots: true },
  safe: { concurrency: 1, delay: 10000, respectRobots: true },
  guided: { concurrency: 1, delay: 2000, respectRobots: true }
};

let currentProfile: ExecutionProfile = 'standard';
let appSettings: any = {
  outputDirectory: '',
  proxy: {},
  caBundlePath: ''
};

export function setupIPC(app: any) {
  // Profile management
  ipcMain.handle(IPC_CHANNELS.PROFILE_GET, async () => {
    return { profile: currentProfile, config: profiles[currentProfile] };
  });

  ipcMain.handle(IPC_CHANNELS.PROFILE_SET, async (_, { profile, overrides }) => {
    if (profiles[profile as ExecutionProfile]) {
      currentProfile = profile as ExecutionProfile;
      if (overrides) {
        profiles[currentProfile] = { ...profiles[currentProfile], ...overrides };
      }
      return { ok: true };
    }
    throw new Error('Invalid profile');
  });

  // Authentication
  ipcMain.handle(IPC_CHANNELS.AUTH_LOGIN, async (_, { url }) => {
    const crawlWindow = app.createCrawlWindow();
    crawlWindow.show();
    if (url) {
      await crawlWindow.loadURL(url);
    }
    return { ok: true };
  });

  // Challenge handling
  ipcMain.handle(IPC_CHANNELS.CHALLENGE_AWAIT_USER_ACTION, async () => {
    // This would typically show a modal and wait for user input
    // For now, return a default action
    return { action: 'continue' };
  });

  // Capture operations
  ipcMain.handle(IPC_CHANNELS.CAPTURE_SINGLEFILE, async (_, { url }) => {
    const crawlWindow = app.createCrawlWindow();
    await crawlWindow.loadURL(url);
    
    // Wait for page to load
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Execute SingleFile capture
    const html = await crawlWindow.webContents.executeJavaScript(`
      if (window.singlefile) {
        return window.singlefile.processCurrentPage();
      }
      return document.documentElement.outerHTML;
    `);
    
    // Save to file
    const filename = url.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.singlefile.html';
    const filePath = path.join(appSettings.outputDirectory, filename);
    fs.writeFileSync(filePath, html);
    
    return { htmlPath: filePath, bytes: html.length };
  });

  ipcMain.handle(IPC_CHANNELS.CAPTURE_PDF, async (_, { singlefileHtmlPath, options }) => {
    const crawlWindow = app.createCrawlWindow();
    await crawlWindow.loadURL(`file://${singlefileHtmlPath}`);
    
    // Wait for content to render
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const pdfOptions = {
      printBackground: true,
      format: 'A4',
      ...options
    };
    
    const data = await crawlWindow.webContents.printToPDF(pdfOptions);
    const pdfPath = singlefileHtmlPath.replace('.singlefile.html', '.pdf');
    fs.writeFileSync(pdfPath, data);
    
    return { pdfPath, bytes: data.length };
  });

  // Queue management
  ipcMain.handle(IPC_CHANNELS.QUEUE_ENQUEUE, async (_, { urls, options }) => {
    const enqueued = queue.addItems(urls, options);
    return { enqueued };
  });

  ipcMain.handle(IPC_CHANNELS.QUEUE_STATUS, async () => {
    return {
      items: queue.getItems(),
      stats: queue.getStats()
    };
  });

  ipcMain.handle(IPC_CHANNELS.QUEUE_PAUSE_ITEM, async (_, { url }) => {
    const ok = queue.pauseItem(url);
    return { ok };
  });

  ipcMain.handle(IPC_CHANNELS.QUEUE_RESUME_ITEM, async (_, { url }) => {
    const ok = queue.resumeItem(url);
    return { ok };
  });

  // Settings
  ipcMain.handle(IPC_CHANNELS.SETTINGS_GET, async () => {
    return appSettings;
  });

  ipcMain.handle(IPC_CHANNELS.SETTINGS_SET, async (_, settings) => {
    appSettings = { ...appSettings, ...settings };
    return { ok: true };
  });

  // Network configuration
  ipcMain.handle(IPC_CHANNELS.CERTS_SET_CA_BUNDLE, async (_, { path }) => {
    // Configure certificate authority bundle
    appSettings.caBundlePath = path;
    return { ok: true };
  });

  ipcMain.handle(IPC_CHANNELS.NETWORK_SET_PROXY, async (_, config) => {
    // Configure proxy settings
    appSettings.proxy = config;
    session.defaultSession.setProxy({
      proxyRules: config.http || config.https
    });
    return { ok: true };
  });

  // Utilities
  ipcMain.handle(IPC_CHANNELS.SHELL_OPEN_EXTERNAL, async (_, { url }) => {
    await shell.openExternal(url);
    return { ok: true };
  });

  ipcMain.handle(IPC_CHANNELS.DIALOG_SHOW_SAVE, async (_, options) => {
    const result = await dialog.showSaveDialog(options);
    return result;
  });

  ipcMain.handle(IPC_CHANNELS.DIALOG_SHOW_OPEN, async (_, options) => {
    const result = await dialog.showOpenDialog(options);
    return result;
  });
}
