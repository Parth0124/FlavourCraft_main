import { api } from '../client';
import type { CuisineCollection } from '../../../types/api.types';

export const cuisineService = {
  async getAllCuisines(userOnly = false) {
    const response = await api.get('/cuisines/', {
      params: { user_only: userOnly }
    });
    return response.data;
  },

  async getCuisineCollection(
    cuisineType: string,
    page = 1,
    limit = 20,
    userOnly = false
  ): Promise<CuisineCollection> {
    const response = await api.get(`/cuisines/${cuisineType}`, {
      params: { 
        skip: (page - 1) * limit,
        limit,
        user_only: userOnly 
      }
    });
    return response.data;
  },

  async getCuisineStats(cuisineType: string, userOnly = false) {
    const response = await api.get(`/cuisines/${cuisineType}/stats`, {
      params: { user_only: userOnly }
    });
    return response.data;
  },

  async searchByCuisineAndIngredients(
    cuisineType: string,
    ingredients: string,
    limit = 20,
    userOnly = false
  ) {
    const response = await api.get(`/cuisines/${cuisineType}/search`, {
      params: { ingredients, limit, user_only: userOnly }
    });
    return response.data;
  },

  async getTrendingCuisines(days = 7, limit = 10) {
    const response = await api.get('/cuisines/trending/now', {
      params: { days, limit }
    });
    return response.data;
  }
};