import { createContext, useContext, useState, useCallback } from 'react';
import { api } from '../api/client';
import { authApi } from '../api/resources';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [tenantId, setTenantId] = useState(() => localStorage.getItem('tenant_id') || null);
  const [isAuthed, setIsAuthed] = useState(() => !!api.getTokens().access);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    api.setTokens(data.access_token, data.refresh_token);
    setIsAuthed(true);
  }, []);

  const logout = useCallback(() => {
    api.clearTokens();
    localStorage.removeItem('tenant_id');
    setIsAuthed(false);
    setTenantId(null);
  }, []);

  const selectTenant = useCallback((id) => {
    localStorage.setItem('tenant_id', id);
    setTenantId(id);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthed, tenantId, login, logout, selectTenant }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
