import { apiClient } from './apiClient';

export async function loginAccount({ email, password }) {
  const { data } = await apiClient.post('/api/auth/login', { email, password });
  return data;
}

export async function registerAccount({ email, fullName, password }) {
  const { data } = await apiClient.post('/api/auth/register', {
    email,
    full_name: fullName,
    password,
  });
  return data;
}

export async function fetchMe() {
  const { data } = await apiClient.get('/api/auth/me');
  return data;
}
