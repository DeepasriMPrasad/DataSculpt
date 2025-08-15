const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let apiProcess;

// Start the FastAPI backend server
function startApiServer() {
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    apiProcess = spawn(pythonPath, ['-m', 'uvicorn', 'apps.api.crawlops_api.main:app', '--host', '0.0.0.0', '--port', '8000'], {
        cwd: path.join(__dirname, '..'),
        stdio: 'pipe'
    });

    apiProcess.stdout.on('data', (data) => {
        console.log(`API: ${data}`);
    });

    apiProcess.stderr.on('data', (data) => {
        console.error(`API Error: ${data}`);
    });

    apiProcess.on('close', (code) => {
        console.log(`API process exited with code ${code}`);
    });
}

function createWindow() {
    // Create the browser window
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            webSecurity: false // Allow local API calls
        },
        icon: path.join(__dirname, '../assets/icon.png'),
        titleBarStyle: 'default',
        show: false
    });

    // Wait for API server to start, then load the frontend
    setTimeout(() => {
        // Load the local web interface
        mainWindow.loadFile(path.join(__dirname, '../index.html'));
    }, 3000);

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// App event handlers
app.whenReady().then(() => {
    // Start the API server
    startApiServer();
    
    // Create the main window
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    // Stop the API server
    if (apiProcess) {
        apiProcess.kill();
    }
    
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    // Clean shutdown of API server
    if (apiProcess) {
        apiProcess.kill();
    }
});

// IPC handlers for additional desktop features
ipcMain.handle('get-app-version', () => {
    return app.getVersion();
});

ipcMain.handle('show-save-dialog', async () => {
    const { dialog } = require('electron');
    return await dialog.showSaveDialog(mainWindow, {
        filters: [
            { name: 'JSON Files', extensions: ['json'] },
            { name: 'Markdown Files', extensions: ['md'] },
            { name: 'HTML Files', extensions: ['html'] },
            { name: 'PDF Files', extensions: ['pdf'] }
        ]
    });
});