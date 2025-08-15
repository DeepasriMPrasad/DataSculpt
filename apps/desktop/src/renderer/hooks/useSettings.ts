import { useState, useEffect } from 'react';
import type { CrawlSettings } from '@shared/types';

const defaultSettings: Partial<CrawlSettings> = {
  outputDirectory: '',
  concurrency: 3,
  delay: 1000,
  respectRobots: true,
  timeout: 30,
  proxy: {},
  caBundlePath: '',
  validateTLS: true,
  followRedirects: true,
  enableLogs: true,
  userAgent: ''
};

export function useSettings() {
  const [settings, setSettings] = useState<Partial<CrawlSettings>>(defaultSettings);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const savedSettings = await window.electronAPI.getSettings();
      setSettings({ ...defaultSettings, ...savedSettings });
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const updateSettings = (updates: Partial<CrawlSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  };

  const saveSettings = async () => {
    try {
      await window.electronAPI.setSettings(settings);
      return true;
    } catch (error) {
      console.error('Failed to save settings:', error);
      return false;
    }
  };

  return {
    settings,
    updateSettings,
    saveSettings
  };
}
