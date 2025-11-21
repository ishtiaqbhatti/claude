import { create } from 'zustand';
import api from '../lib/api';

export const useStore = create((set, get) => ({
  // URL Management State
  urls: [],
  urlsLoading: false,
  urlStats: null,

  // Jobs State
  jobs: [],
  jobsLoading: false,
  jobStats: null,
  selectedJob: null,

  // Scraping State
  scrapingRuns: [],
  activeRuns: [],
  scrapingInProgress: false,

  // Pagination
  pagination: {
    page: 1,
    pageSize: 50,
    total: 0,
    totalPages: 0,
  },

  // URL Actions
  fetchUrls: async (params = {}) => {
    set({ urlsLoading: true });
    try {
      const data = await api.url.getAll(params);
      set({
        urls: data.urls,
        pagination: {
          page: data.page,
          pageSize: data.page_size,
          total: data.total,
          totalPages: data.total_pages,
        },
        urlsLoading: false,
      });
    } catch (error) {
      console.error('Failed to fetch URLs:', error);
      set({ urlsLoading: false });
    }
  },

  fetchUrlStats: async () => {
    try {
      const stats = await api.url.getStats();
      set({ urlStats: stats });
    } catch (error) {
      console.error('Failed to fetch URL stats:', error);
    }
  },

  createUrl: async (urlData) => {
    try {
      await api.url.create(urlData);
      // Refresh URLs after creation
      get().fetchUrls();
      get().fetchUrlStats();
      return { success: true };
    } catch (error) {
      console.error('Failed to create URL:', error);
      return { success: false, error: error.message };
    }
  },

  updateUrl: async (id, urlData) => {
    try {
      await api.url.update(id, urlData);
      // Refresh URLs after update
      get().fetchUrls();
      return { success: true };
    } catch (error) {
      console.error('Failed to update URL:', error);
      return { success: false, error: error.message };
    }
  },

  deleteUrl: async (id) => {
    try {
      await api.url.delete(id);
      // Refresh URLs after deletion
      get().fetchUrls();
      get().fetchUrlStats();
      return { success: true };
    } catch (error) {
      console.error('Failed to delete URL:', error);
      return { success: false, error: error.message };
    }
  },

  toggleUrl: async (id) => {
    try {
      await api.url.toggle(id);
      // Refresh URLs after toggle
      get().fetchUrls();
      get().fetchUrlStats();
      return { success: true };
    } catch (error) {
      console.error('Failed to toggle URL:', error);
      return { success: false, error: error.message };
    }
  },

  // Job Actions
  fetchJobs: async (params = {}) => {
    set({ jobsLoading: true });
    try {
      const data = await api.job.search(params);
      set({
        jobs: data.jobs,
        pagination: {
          page: data.page,
          pageSize: data.page_size,
          total: data.total,
          totalPages: data.total_pages,
        },
        jobsLoading: false,
      });
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
      set({ jobsLoading: false });
    }
  },

  fetchJobStats: async () => {
    try {
      const stats = await api.job.getStats();
      set({ jobStats: stats });
    } catch (error) {
      console.error('Failed to fetch job stats:', error);
    }
  },

  fetchJobById: async (uid) => {
    try {
      const data = await api.job.getById(uid);
      set({ selectedJob: data.job });
      return data.job;
    } catch (error) {
      console.error('Failed to fetch job:', error);
      return null;
    }
  },

  addJob: (job) => {
    set((state) => ({
      jobs: [job, ...state.jobs],
    }));
  },

  updateJob: (uid, updates) => {
    set((state) => ({
      jobs: state.jobs.map((job) =>
        job.uid === uid ? { ...job, ...updates } : job
      ),
      selectedJob:
        state.selectedJob?.uid === uid
          ? { ...state.selectedJob, ...updates }
          : state.selectedJob,
    }));
  },

  deleteJob: async (uid) => {
    try {
      await api.job.delete(uid);
      set((state) => ({
        jobs: state.jobs.filter((job) => job.uid !== uid),
      }));
      return { success: true };
    } catch (error) {
      console.error('Failed to delete job:', error);
      return { success: false, error: error.message };
    }
  },

  // Scraping Actions
  fetchRecentRuns: async (params = {}) => {
    try {
      const data = await api.scraping.getRecentRuns(params);
      set({ scrapingRuns: data.runs });
    } catch (error) {
      console.error('Failed to fetch recent runs:', error);
    }
  },

  fetchActiveRuns: async () => {
    try {
      const data = await api.scraping.getActiveRuns();
      set({ activeRuns: data.runs });
    } catch (error) {
      console.error('Failed to fetch active runs:', error);
    }
  },

  setScrapingInProgress: (inProgress) => {
    set({ scrapingInProgress: inProgress });
  },

  // Reset selected job
  clearSelectedJob: () => {
    set({ selectedJob: null });
  },
}));
