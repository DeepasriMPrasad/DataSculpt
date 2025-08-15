import React, { useState, useEffect } from 'react';
import { Play, Folder, LogIn, AlertCircle } from 'lucide-react';
import { useSettings } from '../hooks/useSettings';

function Dashboard() {
  const { settings, updateSettings } = useSettings();
  const [crawlConfig, setCrawlConfig] = useState({
    startUrl: '',
    depth: 2,
    maxPages: 100,
    allowedDomains: '',
    disallowedPaths: '',
    profile: 'standard' as const,
    formats: {
      json: true,
      markdown: true,
      html: true,
      pdf: false
    },
    crawlPdfLinks: false
  });
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginStatus, setLoginStatus] = useState('');

  const handleStartCrawl = async () => {
    if (!crawlConfig.startUrl) {
      alert('Please enter a start URL');
      return;
    }

    if (!settings.outputDirectory) {
      const result = await window.electronAPI.showSaveDialog({
        title: 'Select Output Directory',
        properties: ['createDirectory']
      });
      
      if (!result.canceled && result.filePath) {
        updateSettings({ outputDirectory: result.filePath });
      } else {
        return;
      }
    }

    try {
      const domains = crawlConfig.allowedDomains.split(',').map(d => d.trim()).filter(Boolean);
      const paths = crawlConfig.disallowedPaths.split(',').map(p => p.trim()).filter(Boolean);

      await window.electronAPI.enqueueURLs([crawlConfig.startUrl], {
        depth: crawlConfig.depth,
        maxPages: crawlConfig.maxPages,
        allowedDomains: domains,
        disallowedPaths: paths,
        profile: crawlConfig.profile,
        formats: crawlConfig.formats,
        crawlPdfLinks: crawlConfig.crawlPdfLinks
      });

      alert('Crawl started! Check the Queue tab for progress.');
    } catch (error) {
      console.error('Failed to start crawl:', error);
      alert('Failed to start crawl. Check console for details.');
    }
  };

  const handleLogin = async () => {
    try {
      setLoginStatus('Opening login window...');
      await window.electronAPI.login(crawlConfig.startUrl);
      setIsLoggedIn(true);
      setLoginStatus('Successfully authenticated');
    } catch (error) {
      console.error('Login failed:', error);
      setLoginStatus('Login failed');
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
          Web Crawling Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure and start your web crawling operations
        </p>
      </div>

      {/* Profile Banner */}
      <div className={`mb-6 p-4 rounded-lg border-l-4 ${
        crawlConfig.profile === 'safe' 
          ? 'bg-yellow-50 border-yellow-400 dark:bg-yellow-900/20' 
          : crawlConfig.profile === 'guided'
          ? 'bg-blue-50 border-blue-400 dark:bg-blue-900/20'
          : 'bg-green-50 border-green-400 dark:bg-green-900/20'
      }`}>
        <div className="flex items-center">
          <AlertCircle className={`h-5 w-5 mr-2 ${
            crawlConfig.profile === 'safe' ? 'text-yellow-600' :
            crawlConfig.profile === 'guided' ? 'text-blue-600' : 'text-green-600'
          }`} />
          <span className="font-medium">
            {crawlConfig.profile === 'safe' && 'Safe-Mode Active - Slow and respectful crawling'}
            {crawlConfig.profile === 'guided' && 'Guided Crawl - Manual review for each page'}
            {crawlConfig.profile === 'standard' && 'Standard Mode - Balanced speed and politeness'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column - Configuration */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Crawl Configuration
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Start URL
                </label>
                <input
                  type="url"
                  value={crawlConfig.startUrl}
                  onChange={(e) => setCrawlConfig({ ...crawlConfig, startUrl: e.target.value })}
                  placeholder="https://example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Max Depth
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={crawlConfig.depth}
                    onChange={(e) => setCrawlConfig({ ...crawlConfig, depth: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Max Pages
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={crawlConfig.maxPages}
                    onChange={(e) => setCrawlConfig({ ...crawlConfig, maxPages: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Allowed Domains (comma-separated)
                </label>
                <input
                  type="text"
                  value={crawlConfig.allowedDomains}
                  onChange={(e) => setCrawlConfig({ ...crawlConfig, allowedDomains: e.target.value })}
                  placeholder="example.com, subdomain.example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Execution Profile
                </label>
                <select
                  value={crawlConfig.profile}
                  onChange={(e) => setCrawlConfig({ ...crawlConfig, profile: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                >
                  <option value="standard">Standard</option>
                  <option value="safe">Safe-Mode</option>
                  <option value="guided">Guided Crawl</option>
                </select>
              </div>
            </div>
          </div>

          {/* Export Formats */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Export Formats
            </h3>
            
            <div className="space-y-3">
              {Object.entries(crawlConfig.formats).map(([format, enabled]) => (
                <label key={format} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) => setCrawlConfig({
                      ...crawlConfig,
                      formats: { ...crawlConfig.formats, [format]: e.target.checked }
                    })}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-gray-700 dark:text-gray-300 capitalize">
                    {format === 'html' ? 'SingleFile HTML' : format}
                  </span>
                </label>
              ))}
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={crawlConfig.crawlPdfLinks}
                  onChange={(e) => setCrawlConfig({ ...crawlConfig, crawlPdfLinks: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Crawl links extracted from PDFs
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Right Column - Actions & Status */}
        <div className="space-y-6">
          {/* Authentication Status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Authentication
            </h3>
            
            <div className="space-y-4">
              <div className={`flex items-center p-3 rounded-md ${
                isLoggedIn ? 'bg-green-50 dark:bg-green-900/20' : 'bg-yellow-50 dark:bg-yellow-900/20'
              }`}>
                <div className={`h-3 w-3 rounded-full mr-3 ${
                  isLoggedIn ? 'bg-green-400' : 'bg-yellow-400'
                }`} />
                <span className="text-sm">
                  {isLoggedIn ? 'Authenticated' : 'Not authenticated'}
                </span>
              </div>
              
              {loginStatus && (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {loginStatus}
                </p>
              )}
              
              <button
                onClick={handleLogin}
                className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <LogIn className="h-4 w-4 mr-2" />
                Login / Authenticate
              </button>
            </div>
          </div>

          {/* Output Directory */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Output Directory
            </h3>
            
            <div className="space-y-4">
              <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                <p className="text-sm text-gray-600 dark:text-gray-400 break-all">
                  {settings.outputDirectory || 'No directory selected'}
                </p>
              </div>
              
              <button
                onClick={handleSelectOutputDir}
                className="w-full flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                <Folder className="h-4 w-4 mr-2" />
                Select Output Directory
              </button>
            </div>
          </div>

          {/* Start Crawl */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <button
              onClick={handleStartCrawl}
              disabled={!crawlConfig.startUrl}
              className="w-full flex items-center justify-center px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-lg font-medium"
            >
              <Play className="h-5 w-5 mr-2" />
              Start Crawl
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
