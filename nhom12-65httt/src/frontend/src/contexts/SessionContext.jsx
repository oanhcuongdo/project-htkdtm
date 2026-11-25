import { createContext, useContext, useEffect, useState } from 'react';
import { fetchMe } from '../services/authService';

const SessionContext = createContext(null);

function getOrCreateSessionId() {
  const key = 'smartrent_session_id';
  let id = localStorage.getItem(key);
  if (!id) {
    id = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    localStorage.setItem(key, id);
  }
  return id;
}

export function SessionProvider({ children }) {
  const [sessionId] = useState(getOrCreateSessionId);
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('smartrent_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    const token = localStorage.getItem('smartrent_token');
    if (token) {
      fetchMe()
        .then((u) => {
          setUser(u);
          localStorage.setItem('smartrent_user', JSON.stringify(u));
        })
        .catch(() => {
          localStorage.removeItem('smartrent_token');
          localStorage.removeItem('smartrent_user');
          setUser(null);
        });
    }
  }, []);

  const setAuthSession = (token, userProfile) => {
    localStorage.setItem('smartrent_token', token);
    localStorage.setItem('smartrent_user', JSON.stringify(userProfile));
    setUser(userProfile);
  };

  const logout = () => {
    localStorage.removeItem('smartrent_token');
    localStorage.removeItem('smartrent_user');
    setUser(null);
  };

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        user,
        isAdmin: user?.role === 'admin',
        setAuthSession,
        logout,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error('useSession must be used within SessionProvider');
  }
  return ctx;
}
