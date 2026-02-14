import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  config => {
    // Add auth token if needed
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API endpoints
export const incidentsAPI = {
  getAll: (params) => api.get('/incidents', { params }),
  getById: (id) => api.get(`/incidents/${id}`),
  getTimeline: (id) => api.get(`/incidents/${id}/timeline`),
  getGraph: (id) => api.get(`/incidents/${id}/graph`),
  updateStatus: (id, data) => api.patch(`/incidents/${id}/status`, data),
  getStats: () => api.get('/incidents/stats/summary')
}

export const copilotAPI = {
  query: (question) => api.post('/copilot/query', { question }, { timeout: 60000 }) // 60s timeout for LLM queries
}

export const liveAPI = {
  getHealth: () => api.get('/live/health'),
  getMetrics: (source) => api.get(`/live/metrics/${source}`)
}

export default api
