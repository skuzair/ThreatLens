import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const incidentsAPI = {
  getAll: (params) => api.get('/incidents', { params }),
  getById: (id) => api.get(`/incidents/${id}`),
  getTimeline: (id) => api.get(`/incidents/${id}/timeline`),
  getGraph: (id) => api.get(`/incidents/${id}/graph`),
  updateStatus: (id, status) => api.patch(`/incidents/${id}/status`, { status }),
};

export const evidenceAPI = {
  getByIncident: (id) => api.get(`/evidence/${id}`),
  verify: (id) => api.get(`/evidence/${id}/verify`),
};

export const sandboxAPI = {
  getByIncident: (id) => api.get(`/sandbox/${id}`),
};

export const iocsAPI = {
  getAll: (params) => api.get('/iocs', { params }),
  block: (id) => api.post(`/iocs/${id}/block`),
};

export const copilotAPI = {
  query: (question) => api.post('/copilot/query', { question }),
};

export const liveAPI = {
  getNetwork: () => api.get('/live/network'),
  getCameras: () => api.get('/live/cameras'),
  getLogins: () => api.get('/live/logins'),
  getRF: () => api.get('/live/rf'),
  getFiles: () => api.get('/live/files'),
  getAnomalyScores: () => api.get('/live/anomaly-scores'),
};

export default api;
