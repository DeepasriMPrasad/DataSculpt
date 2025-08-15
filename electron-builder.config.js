module.exports = {
  "appId": "com.crawlops.studio",
  "productName": "CrawlOps Studio",
  "directories": {
    "output": "dist"
  },
  "files": [
    "dist/**/*",
    "index.js",
    "main.js", 
    "preload.js",
    "session_manager.py",
    "session_api.py",
    "session_frontend.js",
    "unified_server.py",
    "test_api.py",
    "crawl_cache/**/*",
    "node_modules/**/*",
    "!node_modules/@esbuild/aix-ppc64",
    "!node_modules/@esbuild/aix-ppc64/**",
    "!node_modules/@esbuild/android-*/**", 
    "!node_modules/@esbuild/darwin-*/**",
    "!node_modules/@esbuild/freebsd-*/**",
    "!node_modules/@esbuild/linux-*/**",
    "!node_modules/@esbuild/netbsd-*/**",
    "!node_modules/@esbuild/openbsd-*/**",
    "!node_modules/@esbuild/sunos-*/**",
    "!**/test/**",
    "!**/*.md",
    "package.json"
  ],
 "asar": true,
  "win": {
    "target": [
      {
        "target": "nsis",
        "arch": ["x64"]
      },
      {
        "target": "portable",
        "arch": ["x64"]
      }
    ],
    "icon": "icon.ico",
    "requestedExecutionLevel": "asInvoker",
    "publisherName": "CrawlOps Studio",
    "verifyUpdateCodeSignature": false,
    "artifactName": "${productName} Setup ${version}.${ext}",
    "certificateFile": null,
    "certificatePassword": null
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
    "allowElevation": false,
    "allowToChangeInstallationDirectory": true,
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true,
    "displayLanguageSelector": false,
    "installerIcon": "icon.ico",
    "uninstallerIcon": "icon.ico",
    "shortcutName": "CrawlOps Studio",
    "deleteAppDataOnUninstall": false,
    "runAfterFinish": true
  },
  "dmg": {
    "title": "CrawlOps Studio",
    "icon": "icon.icns"
  }
}