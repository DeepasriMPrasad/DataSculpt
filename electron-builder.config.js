module.exports = {
  "appId": "com.crawlops.studio",
  "productName": "CrawlOps Studio",
  "directories": {
    "output": "dist"
  },
  "files": [
    "dist/**/*",
    "main.js",
    "preload.js",
    "session_manager.py",
    "session_api.py",
    "unified_server.py",
    "node_modules/**/*",
    "!node_modules/@esbuild/**",
    "package.json"
  ],
  "win": {
    "target": [
      {
        "target": "nsis",
        "arch": ["x64"]
      }
    ],
    "icon": "icon.ico"
  },
  "mac": {
    "target": [
      {
        "target": "dmg",
        "arch": ["x64", "arm64"]
      }
    ],
    "icon": "icon.icns",
    "category": "public.app-category.developer-tools"
  },
  "linux": {
    "target": [
      {
        "target": "AppImage",
        "arch": ["x64"]
      },
      {
        "target": "deb",
        "arch": ["x64"]
      }
    ],
    "icon": "icon.png",
    "category": "Development"
  },
  "nsis": {
    "oneClick": false,
    "allowElevation": true,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true
  },
  "dmg": {
    "title": "CrawlOps Studio",
    "icon": "icon.icns"
  }
}