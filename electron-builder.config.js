module.exports = {
  "appId": "com.crawlops.studio",
  "productName": "CrawlOps Studio", 
  "directories": {
    "output": "dist"
  },
  "files": [
    "dist/**/*",
    "node_modules/**/*",
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
  "nsis": {
    "oneClick": false,
    "allowElevation": true,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true
  }
}