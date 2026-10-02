const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function getTokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

function setTokens(access, refresh) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) throw new Error('No refresh token');
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) {
    clearTokens();
    throw new Error('Session expired');
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

async function request(path, { method = 'GET', body, skipAuth = false } = {}) {
  const { access } = getTokens();
  const headers = { 'Content-Type': 'application/json' };
  if (!skipAuth && access) headers['Authorization'] = `Bearer ${access}`;

  let res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // One retry after a silent token refresh, for a stale-but-refreshable session
  if (res.status === 401 && !skipAuth) {
    try {
      const newAccess = await refreshAccessToken();
      res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: { ...headers, Authorization: `Bearer ${newAccess}` },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch {
      window.location.href = '/login';
      throw new Error('Session expired');
    }
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const error = new Error(data?.detail || 'Request failed');
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}

export const api = { request, getTokens, setTokens, clearTokens, API_BASE };
