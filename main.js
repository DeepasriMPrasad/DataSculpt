const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let apiProcess;

// Start the FastAPI backend server
function startApiServer() {
    // Use the correct Python executable path based on platform
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    
    console.log('Starting API server with Python path:', pythonPath);
    console.log('Working directory:', __dirname);
    
    // Start the unified server directly from the root directory
    apiProcess = spawn(pythonPath, ['unified_server.py'], {
        cwd: __dirname,
        stdio: 'inherit' // Show output in console for debugging
    });

    apiProcess.stdout.on('data', (data) => {
        console.log(`API: ${data.toString()}`);
    });

    apiProcess.stderr.on('data', (data) => {
        console.error(`API Error: ${data.toString()}`);
    });

    apiProcess.on('close', (code) => {
        console.log(`API process exited with code ${code}`);
    });

    apiProcess.on('error', (error) => {
        console.error('Failed to start API server:', error);
    });
}

function createWindow() {
    // Create the browser window
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        icon: path.join(__dirname, 'icon.ico'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            webSecurity: false // Allow local API calls
        },
        titleBarStyle: 'default',
        show: false
    });

    // Load the built frontend or development server
    if (process.env.NODE_ENV === 'development') {
        mainWindow.loadURL('http://localhost:5000');
        mainWindow.webContents.openDevTools();
    } else {
        // In production, serve from the unified server
        mainWindow.loadURL('http://localhost:5000');
    }

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

// Basic IPC handlers for the application
ipcMain.handle('app:getVersion', () => {
    return app.getVersion();
});

ipcMain.handle('app:quit', () => {
    app.quit();
});

// App event handlers
app.whenReady().then(() => {
    // Only start API server in production builds
    if (process.env.NODE_ENV !== 'development') {
        startApiServer();
    }
    
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