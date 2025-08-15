import { app, BrowserWindow, session, ipcMain } from 'electron';
import * as path from 'path';
import { setupIPC } from './ipc/handlers';
import { loadSingleFile } from './singlefile/loader';

class CrawlOpsApp {
  private mainWindow: BrowserWindow | null = null;
  private crawlWindow: BrowserWindow | null = null;
  private apiProcess: any = null;

  constructor() {
    this.initApp();
  }

  private initApp() {
    app.whenReady().then(() => {
      this.createMainWindow();
      this.setupSessions();
      this.startBackendAPI();
      setupIPC(this);

      app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
          this.createMainWindow();
        }
      });
    });

    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        this.cleanup();
        app.quit();
      }
    });

    app.on('before-quit', () => {
      this.cleanup();
    });
  }

  private createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, '../preload/preload.js'),
        webSecurity: true
      },
      titleBarStyle: 'default',
      show: false
    });

    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.loadURL('http://localhost:5000');
      this.mainWindow.webContents.openDevTools();
    } else {
      this.mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
    }

    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show();
    });
  }

  public createCrawlWindow(): BrowserWindow {
    if (this.crawlWindow && !this.crawlWindow.isDestroyed()) {
      return this.crawlWindow;
    }

    this.crawlWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      show: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        webSecurity: true,
        session: session.fromPartition('crawl-session')
      }
    });

    return this.crawlWindow;
  }

  private async setupSessions() {
    const crawlSession = session.fromPartition('crawl-session');
    
    // Load SingleFile extension or inject core
    await loadSingleFile(crawlSession);
    
    // Setup user agent
    crawlSession.setUserAgent('CrawlOps Studio/1.0');
  }

  private startBackendAPI() {
    const { spawn } = require('child_process');
    
    // Start FastAPI backend
    this.apiProcess = spawn('python', ['-m', 'uvicorn', 'crawlops_api.main:app', '--host', '0.0.0.0', '--port', '8000'], {
      cwd: path.join(__dirname, '../../api'),
      stdio: 'pipe'
    });

    this.apiProcess.stdout.on('data', (data: Buffer) => {
      console.log(`API: ${data.toString()}`);
    });

    this.apiProcess.stderr.on('data', (data: Buffer) => {
      console.error(`API Error: ${data.toString()}`);
    });
  }

  private cleanup() {
    if (this.apiProcess) {
      this.apiProcess.kill();
    }
  }

  public getMainWindow(): BrowserWindow | null {
    return this.mainWindow;
  }

  public getCrawlWindow(): BrowserWindow | null {
    return this.crawlWindow;
  }
}

new CrawlOpsApp();
