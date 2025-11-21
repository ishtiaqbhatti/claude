import { useEffect, useRef, useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Hook for Server-Sent Events (SSE)
 * Handles connection, reconnection, and event listening
 */
export function useSSE(endpoint, options = {}) {
  const {
    enabled = true,
    onEvent = () => {},
    onError = () => {},
    onComplete = () => {},
  } = options;

  const [status, setStatus] = useState('idle'); // idle, connecting, connected, error, complete
  const [events, setEvents] = useState([]);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!enabled || !endpoint) {
      return;
    }

    let url = endpoint;
    if (!endpoint.startsWith('http')) {
      url = `${API_BASE_URL}${endpoint}`;
    }

    setStatus('connecting');
    setEvents([]);

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('SSE connection opened:', url);
      setStatus('connected');
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      setStatus('error');
      onError(error);
      eventSource.close();
    };

    // Listen for all event types
    const eventTypes = [
      'run_started',
      'url_started',
      'url_completed',
      'job_started',
      'job_completed',
      'run_completed',
      'run_failed',
      'progress',
      'complete',
      'message',
    ];

    eventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (e) => {
        try {
          const data = JSON.parse(e.data);
          const event = { type: eventType, data };

          setEvents((prev) => [...prev, event]);
          onEvent(event);

          // Handle completion events
          if (eventType === 'run_completed' || eventType === 'complete') {
            setStatus('complete');
            onComplete(event);
            setTimeout(() => {
              eventSource.close();
            }, 1000);
          }

          if (eventType === 'run_failed') {
            setStatus('error');
            onError(event);
            setTimeout(() => {
              eventSource.close();
            }, 1000);
          }
        } catch (error) {
          console.error('Failed to parse SSE event:', error);
        }
      });
    });

    // Cleanup on unmount
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [endpoint, enabled]);

  const close = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      setStatus('idle');
    }
  };

  return {
    status,
    events,
    close,
  };
}

/**
 * Hook for starting a search scrape with SSE
 */
export function useSearchScrape() {
  const [isRunning, setIsRunning] = useState(false);
  const [endpoint, setEndpoint] = useState(null);
  const [progress, setProgress] = useState({
    total: 0,
    completed: 0,
    current: null,
  });

  const { status, events, close } = useSSE(endpoint, {
    enabled: isRunning,
    onEvent: (event) => {
      if (event.type === 'url_started') {
        setProgress((prev) => ({
          ...prev,
          current: event.data.url,
        }));
      }
      if (event.type === 'url_completed') {
        setProgress((prev) => ({
          ...prev,
          completed: prev.completed + 1,
        }));
      }
    },
    onComplete: () => {
      setIsRunning(false);
      setEndpoint(null);
    },
    onError: () => {
      setIsRunning(false);
      setEndpoint(null);
    },
  });

  const startScrape = async (urlIds = null) => {
    try {
      const body = {
        url_ids: urlIds,
        triggered_by: 'frontend',
      };

      // Start SSE stream
      const url = `/api/scraping/search/start`;
      setEndpoint(`${url}?url_ids=${urlIds ? urlIds.join(',') : ''}`);
      setIsRunning(true);
      setProgress({ total: 0, completed: 0, current: null });

      return { success: true };
    } catch (error) {
      console.error('Failed to start search scrape:', error);
      setIsRunning(false);
      return { success: false, error: error.message };
    }
  };

  const stopScrape = () => {
    close();
    setIsRunning(false);
    setEndpoint(null);
  };

  return {
    isRunning,
    status,
    events,
    progress,
    startScrape,
    stopScrape,
  };
}

/**
 * Hook for starting a detail scrape with SSE
 */
export function useDetailScrape() {
  const [isRunning, setIsRunning] = useState(false);
  const [endpoint, setEndpoint] = useState(null);
  const [progress, setProgress] = useState({
    total: 0,
    completed: 0,
    current: null,
  });

  const { status, events, close } = useSSE(endpoint, {
    enabled: isRunning,
    onEvent: (event) => {
      if (event.type === 'job_started') {
        setProgress((prev) => ({
          ...prev,
          current: event.data.job_uid,
        }));
      }
      if (event.type === 'job_completed') {
        setProgress((prev) => ({
          ...prev,
          completed: prev.completed + 1,
        }));
      }
    },
    onComplete: () => {
      setIsRunning(false);
      setEndpoint(null);
    },
    onError: () => {
      setIsRunning(false);
      setEndpoint(null);
    },
  });

  const startScrape = async (jobUids = null, limit = 50) => {
    try {
      const params = new URLSearchParams({
        triggered_by: 'frontend',
        limit: limit.toString(),
      });

      if (jobUids) {
        params.append('job_uids', jobUids.join(','));
      }

      const url = `/api/scraping/detail/start?${params.toString()}`;
      setEndpoint(url);
      setIsRunning(true);
      setProgress({ total: jobUids?.length || limit, completed: 0, current: null });

      return { success: true };
    } catch (error) {
      console.error('Failed to start detail scrape:', error);
      setIsRunning(false);
      return { success: false, error: error.message };
    }
  };

  const stopScrape = () => {
    close();
    setIsRunning(false);
    setEndpoint(null);
  };

  return {
    isRunning,
    status,
    events,
    progress,
    startScrape,
    stopScrape,
  };
}
