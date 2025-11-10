import { api } from '../client';
import { apiClient } from '../client';
import type { User, LoginRequest, RegisterRequest, AuthTokens } from '../../../types/api.types';

export const authService = {
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  async login(data: LoginRequest): Promise<AuthTokens> {
    const response = await api.post('/auth/login', data);
    // Store tokens
    apiClient.setToken(response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me');
    return response.data;
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout');
    apiClient.clearToken();
  }
};