import React from 'react';
import { useSettings } from '../hooks/useSettings';
import { Save, Folder, Shield, Network, FileText } from 'lucide-react';

function Settings() {
  const { settings, updateSettings } = useSettings();

  const handleSave = async () => {
    try {
      await window.electronAPI.setSettings(settings);
      alert('Settings saved successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings. Check console for details.');
    }
  };

  const handleSelectCertBundle = async () => {
    const result = await window.electronAPI.showOpenDialog({
      title: 'Select CA Bundle',
      filters: [
        { name: 'Certificate Files', extensions: ['pem', 'crt', 'cer', 'ca-bundle'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
      updateSettings({ caBundlePath: result.filePaths[0] });
    }
  };

  const handleSelectOutputDir = async () => {
    const result = await window.electronAPI.showOpenDialog({
      title: 'Select Output Directory',
      properties: ['openDirectory', 'createDirectory']
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
      updateSettings({ outputDirectory: result.filePaths[0] });
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure application preferences and network settings
        </p>
      </div>

      <div className="space-y-8">
        {/* General Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center mb-4">
            <FileText className="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              General Settings
            </h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Output Directory
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={settings.outputDirectory || ''}
                  onChange={(e) => updateSettings({ outputDirectory: e.target.value })}
                  placeholder="/path/to/output/directory"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <button
                  onClick={handleSelectOutputDir}
                  className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  <Folder className="h-4 w-4 mr-2" />
                  Browse
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Concurrency
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.concurrency || 3}
                  onChange={(e) => updateSettings({ concurrency: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Delay (ms)
                </label>
                <input
                  type="number"
                  min="0"
                  value={settings.delay || 1000}
                  onChange={(e) => updateSettings({ delay: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Request Timeout (s)
                </label>
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={settings.timeout || 30}
                  onChange={(e) => updateSettings({ timeout: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.respectRobots ?? true}
                  onChange={(e) => updateSettings({ respectRobots: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Respect robots.txt files
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.enableLogs ?? true}
                  onChange={(e) => updateSettings({ enableLogs: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Enable detailed logging
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Network Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center mb-4">
            <Network className="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Network Settings
            </h2>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  HTTP Proxy
                </label>
                <input
                  type="text"
                  value={settings.proxy?.http || ''}
                  onChange={(e) => updateSettings({ 
                    proxy: { ...settings.proxy, http: e.target.value }
                  })}
                  placeholder="http://proxy:8080"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  HTTPS Proxy
                </label>
                <input
                  type="text"
                  value={settings.proxy?.https || ''}
                  onChange={(e) => updateSettings({ 
                    proxy: { ...settings.proxy, https: e.target.value }
                  })}
                  placeholder="https://proxy:8080"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                User Agent
              </label>
              <input
                type="text"
                value={settings.userAgent || ''}
                onChange={(e) => updateSettings({ userAgent: e.target.value })}
                placeholder="CrawlOps Studio/1.0 (default if empty)"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-gray-600 dark:text-gray-400 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Security Settings
            </h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Custom CA Bundle
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={settings.caBundlePath || ''}
                  onChange={(e) => updateSettings({ caBundlePath: e.target.value })}
                  placeholder="/path/to/ca-bundle.pem"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <button
                  onClick={handleSelectCertBundle}
                  className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  <Folder className="h-4 w-4 mr-2" />
                  Browse
                </button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Required for corporate networks with custom certificate authorities
              </p>
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.validateTLS ?? true}
                  onChange={(e) => updateSettings({ validateTLS: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Validate TLS certificates
                </span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.followRedirects ?? true}
                  onChange={(e) => updateSettings({ followRedirects: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Follow redirects automatically
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="flex items-center px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <Save className="h-4 w-4 mr-2" />
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;
