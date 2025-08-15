import React from 'react';
import { 
  Globe, 
  List, 
  AlertCircle, 
  Settings as SettingsIcon, 
  Moon, 
  Sun 
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  currentPage: string;
  onPageChange: (page: string) => void;
  isDark: boolean;
  onThemeToggle: () => void;
}

function Layout({ children, currentPage, onPageChange, isDark, onThemeToggle }: LayoutProps) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Globe },
    { id: 'queue', label: 'Queue', icon: List },
    { id: 'challenges', label: 'Challenges', icon: AlertCircle },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-800 shadow-lg">
        <div className="p-6">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">
            CrawlOps Studio
          </h1>
        </div>
        
        <nav className="mt-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`w-full flex items-center px-6 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 ${
                  isActive 
                    ? 'bg-primary-50 text-primary-600 dark:bg-primary-900 dark:text-primary-300 border-r-2 border-primary-600' 
                    : 'text-gray-700 dark:text-gray-300'
                }`}
              >
                <Icon className="mr-3 h-5 w-5" />
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-4 left-4">
          <button
            onClick={onThemeToggle}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
          >
            {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-auto">
          {children}
        </div>
      </div>
    </div>
  );
}

export default Layout;
