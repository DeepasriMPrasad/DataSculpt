import React, { useState, useEffect } from 'react';
import { useQueue } from '../hooks/useQueue';
import { Play, Pause, SkipForward, Eye, Download, RefreshCw } from 'lucide-react';
import type { URLItem } from '@shared/types';

function Queue() {
  const { items, stats, refreshQueue, pauseItem, resumeItem } = useQueue();
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    // Refresh queue every 2 seconds
    const interval = setInterval(refreshQueue, 2000);
    return () => clearInterval(interval);
  }, [refreshQueue]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'done': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      case 'waiting_captcha': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      case 'waiting_user': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
      case 'skipped': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'waiting_captcha': return 'WAITING CAPTCHA';
      case 'waiting_user': return 'WAITING USER';
      default: return status.toUpperCase();
    }
  };

  const filteredItems = items.filter(item => {
    if (filter === 'all') return true;
    return item.status === filter;
  });

  const handleOpenOutput = async (item: URLItem, outputType: string) => {
    if (!item.outputs) return;
    
    let path = '';
    switch (outputType) {
      case 'html':
        path = item.outputs.singlefileHtmlPath || '';
        break;
      case 'pdf':
        path = item.outputs.pdfPath || '';
        break;
      case 'json':
        path = item.outputs.jsonPath || '';
        break;
      case 'md':
        path = item.outputs.mdPath || '';
        break;
    }
    
    if (path) {
      await window.electronAPI.openExternal(`file://${path}`);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Crawl Queue
          </h1>
          <button
            onClick={refreshQueue}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.running}</div>
            <div className="text-sm text-blue-600 dark:text-blue-400">Running</div>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.waiting}</div>
            <div className="text-sm text-yellow-600 dark:text-yellow-400">Waiting</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.done}</div>
            <div className="text-sm text-green-600 dark:text-green-400">Completed</div>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">{stats.failed}</div>
            <div className="text-sm text-red-600 dark:text-red-400">Failed</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
            <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">{stats.total}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2 mb-6">
          {['all', 'running', 'waiting_captcha', 'waiting_user', 'done', 'failed'].map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                filter === status
                  ? 'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600'
              }`}
            >
              {status === 'all' ? 'All' : getStatusLabel(status)}
            </button>
          ))}
        </div>
      </div>

      {/* Queue Items */}
      <div className="space-y-4">
        {filteredItems.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-600 text-lg">
              No items in queue
            </div>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Start a crawl from the Dashboard to see items here
            </p>
          </div>
        ) : (
          filteredItems.map((item) => (
            <div
              key={item.url}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                      {getStatusLabel(item.status)}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Depth: {item.depth} | Profile: {item.profile} | Attempts: {item.attempts}
                    </span>
                  </div>
                  
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate mb-2">
                    {item.url}
                  </h3>

                  {item.error && (
                    <div className="text-sm text-red-600 dark:text-red-400 mb-2">
                      Error: {item.error}
                    </div>
                  )}

                  {/* Format indicators */}
                  <div className="flex gap-2 mb-3">
                    {Object.entries(item.formats).map(([format, enabled]) => (
                      enabled && (
                        <span
                          key={format}
                          className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300"
                        >
                          {format.toUpperCase()}
                        </span>
                      )
                    ))}
                  </div>

                  {/* Output files */}
                  {item.outputs && (
                    <div className="flex gap-2">
                      {item.outputs.singlefileHtmlPath && (
                        <button
                          onClick={() => handleOpenOutput(item, 'html')}
                          className="text-xs text-primary-600 hover:text-primary-800 dark:text-primary-400 flex items-center"
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          HTML
                        </button>
                      )}
                      {item.outputs.pdfPath && (
                        <button
                          onClick={() => handleOpenOutput(item, 'pdf')}
                          className="text-xs text-primary-600 hover:text-primary-800 dark:text-primary-400 flex items-center"
                        >
                          <Download className="h-3 w-3 mr-1" />
                          PDF
                        </button>
                      )}
                      {item.outputs.jsonPath && (
                        <button
                          onClick={() => handleOpenOutput(item, 'json')}
                          className="text-xs text-primary-600 hover:text-primary-800 dark:text-primary-400 flex items-center"
                        >
                          <Download className="h-3 w-3 mr-1" />
                          JSON
                        </button>
                      )}
                      {item.outputs.mdPath && (
                        <button
                          onClick={() => handleOpenOutput(item, 'md')}
                          className="text-xs text-primary-600 hover:text-primary-800 dark:text-primary-400 flex items-center"
                        >
                          <Download className="h-3 w-3 mr-1" />
                          MD
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 ml-4">
                  {item.status === 'running' && (
                    <button
                      onClick={() => pauseItem(item.url)}
                      className="p-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                      title="Pause"
                    >
                      <Pause className="h-4 w-4" />
                    </button>
                  )}
                  
                  {(item.status === 'waiting_user' || item.status === 'waiting_captcha') && (
                    <button
                      onClick={() => resumeItem(item.url)}
                      className="p-2 text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-200"
                      title="Resume"
                    >
                      <Play className="h-4 w-4" />
                    </button>
                  )}
                  
                  {item.status === 'failed' && (
                    <button
                      className="p-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
                      title="Retry"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Queue;
