import React, { useState, useEffect } from 'react';
import { AlertTriangle, Eye, RotateCcw, SkipForward, X, ExternalLink } from 'lucide-react';

interface Challenge {
  id: string;
  url: string;
  type: 'captcha' | 'auth' | 'manual';
  provider?: string;
  description: string;
  createdAt: string;
  screenshotPath?: string;
}

function ChallengeCenter() {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [selectedChallenge, setSelectedChallenge] = useState<Challenge | null>(null);

  useEffect(() => {
    // Listen for captcha detection events
    window.electronAPI.onCaptchaDetected((data) => {
      const newChallenge: Challenge = {
        id: Date.now().toString(),
        url: data.url,
        type: 'captcha',
        provider: data.provider,
        description: `CAPTCHA detected on ${new URL(data.url).hostname}`,
        createdAt: new Date().toISOString(),
        screenshotPath: data.screenshotPath
      };
      
      setChallenges(prev => [newChallenge, ...prev]);
    });

    // Mock some challenges for demonstration
    setChallenges([
      {
        id: '1',
        url: 'https://example.com/login',
        type: 'auth',
        description: 'Authentication required for example.com',
        createdAt: new Date(Date.now() - 300000).toISOString()
      },
      {
        id: '2',
        url: 'https://secure-site.com/page',
        type: 'captcha',
        provider: 'recaptcha',
        description: 'reCAPTCHA challenge detected',
        createdAt: new Date(Date.now() - 600000).toISOString()
      }
    ]);
  }, []);

  const handleAction = async (challenge: Challenge, action: 'continue' | 'retry' | 'skip' | 'abort') => {
    try {
      // Send the action to the main process
      const result = await window.electronAPI.awaitUserAction();
      
      // Remove the challenge from the list
      setChallenges(prev => prev.filter(c => c.id !== challenge.id));
      setSelectedChallenge(null);
      
      console.log(`Challenge ${challenge.id} resolved with action: ${action}`);
    } catch (error) {
      console.error('Failed to handle challenge action:', error);
    }
  };

  const openInBrowser = async (url: string) => {
    try {
      await window.electronAPI.login(url);
    } catch (error) {
      console.error('Failed to open URL in browser:', error);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'captcha':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'auth':
        return <AlertTriangle className="h-5 w-5 text-blue-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'captcha':
        return 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800';
      case 'auth':
        return 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800';
      default:
        return 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800';
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Challenge Center
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage authentication challenges, CAPTCHAs, and manual interventions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Challenge List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Active Challenges ({challenges.length})
            </h2>
          </div>

          {challenges.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <div className="text-gray-600 dark:text-gray-400 text-lg">
                No active challenges
              </div>
              <p className="text-gray-500 dark:text-gray-500 mt-2">
                Challenges will appear here when authentication or CAPTCHAs are required
              </p>
            </div>
          ) : (
            challenges.map((challenge) => (
              <div
                key={challenge.id}
                className={`p-4 rounded-lg border-l-4 cursor-pointer hover:shadow-md transition-shadow ${getTypeColor(challenge.type)} ${
                  selectedChallenge?.id === challenge.id ? 'ring-2 ring-primary-500' : ''
                }`}
                onClick={() => setSelectedChallenge(challenge)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {getTypeIcon(challenge.type)}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                        {challenge.description}
                      </h3>
                      <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                        {challenge.url}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        {formatTime(challenge.createdAt)}
                        {challenge.provider && ` • ${challenge.provider}`}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Challenge Details */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
          {selectedChallenge ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Challenge Details
                </h2>
                <button
                  onClick={() => setSelectedChallenge(null)}
                  className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    URL
                  </label>
                  <div className="flex items-center space-x-2">
                    <p className="text-sm text-gray-900 dark:text-white break-all flex-1">
                      {selectedChallenge.url}
                    </p>
                    <button
                      onClick={() => openInBrowser(selectedChallenge.url)}
                      className="p-1 text-primary-600 hover:text-primary-800 dark:text-primary-400"
                      title="Open in browser"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Type
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white capitalize">
                    {selectedChallenge.type}
                    {selectedChallenge.provider && ` (${selectedChallenge.provider})`}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Description
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {selectedChallenge.description}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Created
                  </label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {new Date(selectedChallenge.createdAt).toLocaleString()}
                  </p>
                </div>

                {selectedChallenge.screenshotPath && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Screenshot
                    </label>
                    <img
                      src={`file://${selectedChallenge.screenshotPath}`}
                      alt="Challenge screenshot"
                      className="max-w-full h-auto border rounded-lg"
                    />
                  </div>
                )}

                {/* Action Buttons */}
                <div className="border-t pt-4 mt-6">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Actions
                  </h3>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => handleAction(selectedChallenge, 'continue')}
                      className="flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      Continue
                    </button>
                    
                    <button
                      onClick={() => handleAction(selectedChallenge, 'retry')}
                      className="flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <RotateCcw className="h-4 w-4 mr-2" />
                      Retry
                    </button>
                    
                    <button
                      onClick={() => handleAction(selectedChallenge, 'skip')}
                      className="flex items-center justify-center px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    >
                      <SkipForward className="h-4 w-4 mr-2" />
                      Skip
                    </button>
                    
                    <button
                      onClick={() => handleAction(selectedChallenge, 'abort')}
                      className="flex items-center justify-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                    >
                      <X className="h-4 w-4 mr-2" />
                      Abort
                    </button>
                  </div>

                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      <strong>Continue:</strong> Proceed after resolving the challenge manually<br />
                      <strong>Retry:</strong> Attempt to access the URL again<br />
                      <strong>Skip:</strong> Skip this URL and continue with others<br />
                      <strong>Abort:</strong> Stop crawling and remove from queue
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <div className="text-gray-600 dark:text-gray-400 text-lg">
                Select a challenge
              </div>
              <p className="text-gray-500 dark:text-gray-500 mt-2">
                Click on a challenge from the list to view details and available actions
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ChallengeCenter;
