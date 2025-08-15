import { useState, useCallback } from 'react';
import type { URLItem, QueueStats } from '@shared/types';

export function useQueue() {
  const [items, setItems] = useState<URLItem[]>([]);
  const [stats, setStats] = useState<QueueStats>({
    running: 0,
    waiting: 0,
    done: 0,
    failed: 0,
    total: 0
  });

  const refreshQueue = useCallback(async () => {
    try {
      const result = await window.electronAPI.getQueueStatus();
      setItems(result.items || []);
      setStats(result.stats || {
        running: 0,
        waiting: 0,
        done: 0,
        failed: 0,
        total: 0
      });
    } catch (error) {
      console.error('Failed to refresh queue:', error);
    }
  }, []);

  const pauseItem = useCallback(async (url: string) => {
    try {
      const result = await window.electronAPI.pauseItem(url);
      if (result.ok) {
        await refreshQueue();
      }
      return result.ok;
    } catch (error) {
      console.error('Failed to pause item:', error);
      return false;
    }
  }, [refreshQueue]);

  const resumeItem = useCallback(async (url: string) => {
    try {
      const result = await window.electronAPI.resumeItem(url);
      if (result.ok) {
        await refreshQueue();
      }
      return result.ok;
    } catch (error) {
      console.error('Failed to resume item:', error);
      return false;
    }
  }, [refreshQueue]);

  return {
    items,
    stats,
    refreshQueue,
    pauseItem,
    resumeItem
  };
}
