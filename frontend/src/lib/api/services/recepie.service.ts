import { api } from '../client';
import type { 
  RecipeGenerationRequest, 
  GeneratedRecipeResponse,
  StaticRecipe 
} from '../../../types/api.types';

export const recipeService = {
  // Generated Recipes
  async generateRecipe(data: RecipeGenerationRequest): Promise<GeneratedRecipeResponse> {
    const response = await api.post('/recipes/generate', data);
    return response.data;
  },

  async getHistory(page = 1, pageSize = 10) {
    const response = await api.get('/recipes/history', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  async getGeneratedRecipe(id: string): Promise<GeneratedRecipeResponse> {
    const response = await api.get(`/recipes/generated/${id}`);
    return response.data;
  },

  async toggleFavorite(recipeId: string) {
    const response = await api.put(`/recipes/generated/${recipeId}/favorite`);
    return response.data;
  },

  async getFavorites(page = 1, pageSize = 10) {
    const response = await api.get('/recipes/favorites', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  // Static Recipes
  async getStaticRecipes(page = 1, pageSize = 20) {
    const response = await api.get('/recipes/static', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  async searchStaticRecipes(filters: {
    tags?: string;
    ingredients?: string;
    difficulty?: string;
    max_prep_time?: number;
    max_cook_time?: number;
  }) {
    const response = await api.get('/recipes/static/search', { params: filters });
    return response.data;
  },

  async getStaticRecipe(id: string): Promise<StaticRecipe> {
    const response = await api.get(`/recipes/static/${id}`);
    return response.data;
  }
};