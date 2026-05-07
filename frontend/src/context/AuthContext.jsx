import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    const response = await authAPI.login({ username, password });
    const { token, user: userData } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (e) {
      // ignore
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const hasRole = (roles) => {
    if (!user) return false;
    const userType = user.user_type.toLowerCase();
    return roles.some(role => userType.includes(role.toLowerCase()));
  };

  const roleLevel = (() => {
    if (!user) return 0;
    const ut = user.user_type.toLowerCase();
    if (ut.includes('director') && !ut.includes('kg')) return 100;
    if (ut.includes('vice')) return 80;
    if (ut.includes('supervisor')) return 70;
    if (ut.includes('kg')) return 60;
    if (ut.includes('room teacher')) return 50;
    if (ut.includes('subject teacher')) return 45;
    if (ut.includes('student')) return 20;
    if (ut.includes('parent')) return 15;
    return 0;
  })();

  return (
    <AuthContext.Provider value={{ user, login, logout, hasRole, roleLevel, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
