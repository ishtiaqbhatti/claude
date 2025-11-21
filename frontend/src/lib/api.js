// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper function for making API requests
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Request failed' }));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

// URL Management API
export const urlApi = {
  getAll: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/api/urls?${queryString}`);
  },

  getById: (id) => apiRequest(`/api/urls/${id}`),

  getEnabled: () => apiRequest('/api/urls/enabled'),

  getStats: () => apiRequest('/api/urls/stats'),

  create: (data) => apiRequest('/api/urls', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  update: (id, data) => apiRequest(`/api/urls/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  }),

  delete: (id) => apiRequest(`/api/urls/${id}`, {
    method: 'DELETE',
  }),

  toggle: (id) => apiRequest(`/api/urls/${id}/toggle`, {
    method: 'POST',
  }),
};

// Job API
export const jobApi = {
  search: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/api/jobs?${queryString}`);
  },

  getById: (uid) => apiRequest(`/api/jobs/${uid}`),

  getStats: () => apiRequest('/api/jobs/stats'),

  getRelated: (uid, limit = 10) =>
    apiRequest(`/api/jobs/${uid}/related?limit=${limit}`),

  getRecentDiscovered: (limit = 20) =>
    apiRequest(`/api/jobs/recent/discovered?limit=${limit}`),

  getPendingEnrichment: (limit = 50) =>
    apiRequest(`/api/jobs/pending/enrichment?limit=${limit}`),

  delete: (uid) => apiRequest(`/api/jobs/${uid}`, {
    method: 'DELETE',
  }),

  updateStatus: (uid, status) => apiRequest(`/api/jobs/${uid}/status?status=${status}`, {
    method: 'PATCH',
  }),

  bulkUpdateStatus: (uids, status) => apiRequest('/api/jobs/bulk/status', {
    method: 'POST',
    body: JSON.stringify({ uids, status }),
  }),
};

// Scraping API
export const scrapingApi = {
  getRecentRuns: (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    return apiRequest(`/api/scraping/runs/recent?${queryString}`);
  },

  getRun: (runId) => apiRequest(`/api/scraping/runs/${runId}`),

  getStats: (runType) => {
    const query = runType ? `?run_type=${runType}` : '';
    return apiRequest(`/api/scraping/runs/stats${query}`);
  },

  getActiveRuns: () => apiRequest('/api/scraping/status/active'),
};

// Health API
export const healthApi = {
  check: () => apiRequest('/api/health'),
};

export default {
  url: urlApi,
  job: jobApi,
  scraping: scrapingApi,
  health: healthApi,
};
