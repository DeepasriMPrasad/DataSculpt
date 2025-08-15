import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Queue from './components/Queue';
import ChallengeCenter from './components/ChallengeCenter';
import Settings from './components/Settings';

type Page = 'dashboard' | 'queue' | 'challenges' | 'settings';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [isDark, setIsDark] = useState(false);

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'queue':
        return <Queue />;
      case 'challenges':
        return <ChallengeCenter />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className={isDark ? 'dark' : ''}>
      <Layout
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        isDark={isDark}
        onThemeToggle={() => setIsDark(!isDark)}
      >
        {renderPage()}
      </Layout>
    </div>
  );
}

export default App;
