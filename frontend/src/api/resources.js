import { api } from './client';

export const authApi = {
  register: (email, password) =>
    api.request('/auth/register', { method: 'POST', body: { email, password }, skipAuth: true }),
  login: (email, password) =>
    api.request('/auth/login', { method: 'POST', body: { email, password }, skipAuth: true }),
};

export const tenantApi = {
  create: (name) => api.request('/tenants', { method: 'POST', body: { name } }),
  members: (tenantId) => api.request(`/tenants/${tenantId}/members`),
  invite: (tenantId, email, role) =>
    api.request(`/tenants/${tenantId}/invite`, { method: 'POST', body: { email, role } }),
};

export const leadApi = {
  list: (tenantId) => api.request(`/tenants/${tenantId}/leads`),
  dueToday: (tenantId) => api.request(`/tenants/${tenantId}/leads/due-today`),
  pipelineSummary: (tenantId) => api.request(`/tenants/${tenantId}/leads/pipeline-summary`),
  create: (tenantId, payload) =>
    api.request(`/tenants/${tenantId}/leads`, { method: 'POST', body: payload }),
  update: (tenantId, leadId, payload) =>
    api.request(`/tenants/${tenantId}/leads/${leadId}`, { method: 'PATCH', body: payload }),
  addActivity: (tenantId, leadId, note) =>
    api.request(`/tenants/${tenantId}/leads/${leadId}/activity`, { method: 'POST', body: { note } }),
};

export const billingApi = {
  status: (tenantId) => api.request(`/tenants/${tenantId}/billing-status`),
  createCheckoutSession: (tenantId) =>
    api.request(`/tenants/${tenantId}/billing/checkout-session`, { method: 'POST' }),
};
