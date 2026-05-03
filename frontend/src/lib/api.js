import Cookies from 'js-cookie';

const API_BASE_URL = '/api'; // Vite proxy handles this in dev, Flask static in prod

export async function apiFetch(endpoint, options = {}) {
  const token = Cookies.get('jwt');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'API request failed');
  }

  return response.json();
}
