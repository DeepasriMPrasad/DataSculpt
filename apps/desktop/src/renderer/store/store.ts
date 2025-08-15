import { create } from 'zustand';
import type { URLItem, QueueStats, CrawlSettings, ExecutionProfile, ChallengeInfo } from '@shared/types';

interface AppState {
  // Queue state
  queueItems: URLItem[];
  queueStats: QueueStats;
  
  // Settings state
  settings: Partial<CrawlSettings>;
  currentProfile: ExecutionProfile;
  
  // Challenge state
  activeChallenges: ChallengeInfo[];
  
  // UI state
  isDarkMode: boolean;
  currentPage: string;
  
  // Actions
  setQueueItems: (items: URLItem[]) => void;
  setQueueStats: (stats: QueueStats) => void;
  updateSettings: (settings: Partial<CrawlSettings>) => void;
  setProfile: (profile: ExecutionProfile) => void;
  addChallenge: (challenge: ChallengeInfo) => void;
  removeChallenge: (url: string) => void;
  setDarkMode: (isDark: boolean) => void;
  setCurrentPage: (page: string) => void;
}

const useAppStore = create<AppState>((set) => ({
  // Initial state
  queueItems: [],
  queueStats: {
    running: 0,
    waiting: 0,
    done: 0,
    failed: 0,
    total: 0
  },
  settings: {},
  currentProfile: 'standard',
  activeChallenges: [],
  isDarkMode: false,
  currentPage: 'dashboard',
  
  // Actions
  setQueueItems: (items) => set({ queueItems: items }),
  setQueueStats: (stats) => set({ queueStats: stats }),
  updateSettings: (newSettings) => set((state) => ({ 
    settings: { ...state.settings, ...newSettings }
  })),
  setProfile: (profile) => set({ currentProfile: profile }),
  addChallenge: (challenge) => set((state) => ({
    activeChallenges: [challenge, ...state.activeChallenges]
  })),
  removeChallenge: (url) => set((state) => ({
    activeChallenges: state.activeChallenges.filter(c => c.url !== url)
  })),
  setDarkMode: (isDark) => set({ isDarkMode: isDark }),
  setCurrentPage: (page) => set({ currentPage: page }),
}));

export default useAppStore;
