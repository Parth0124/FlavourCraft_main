import { api } from '../client';
import type { User, UserPreferences } from '../../../types/api.types';

export const userService = {
  async getProfile(): Promise<User> {
    const response = await api.get('/users/profile');
    return response.data;
  },

  async updateProfile(data: {
    username?: string;
    preferences?: UserPreferences;
  }): Promise<User> {
    const response = await api.put('/users/profile', data);
    return response.data;
  },

  async getUserHistory() {
    const response = await api.get('/users/history');
    return response.data;
  },

  async getUserFavorites() {
    const response = await api.get('/users/favorites');
    return response.data;
  },

  async deleteAccount() {
    const response = await api.delete('/users/account');
    return response.data;
  }
};