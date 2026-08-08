import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  const response = await client.get('/api/health');
  return response.data;
};

export const getFilters = async () => {
  const response = await client.get('/api/filters');
  return response.data;
};

export const getRankings = async (params = {}) => {
  const response = await client.get('/api/rankings', { params });
  return response.data;
};

export const getRouterDetail = async (routerId) => {
  const response = await client.get(`/api/routers/${encodeURIComponent(routerId)}`);
  return response.data;
};

export const askCopilot = async (payload) => {
  const response = await client.post('/api/copilot/ask', payload);
  return response.data;
};

export default client;
