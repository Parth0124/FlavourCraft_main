import { api } from '../client';
import type { 
  RecipeGenerationRequest, 
  GeneratedRecipeResponse,
  StaticRecipe 
} from '../../../types/api.types';

export const recipeService = {
  // ✅ Generated Recipes - properly sends all data including image_urls
  async generateRecipe(data: RecipeGenerationRequest): Promise<GeneratedRecipeResponse> {
    console.log("📤 API Service: Sending recipe generation request:", data);
    
    // ✅ Verify image_urls are present
    if (data.image_urls) {
      console.log("✅ API Service: image_urls included in request:", data.image_urls);
    } else {
      console.warn("⚠️  API Service: No image_urls in request");
    }
    
    const response = await api.post('/recipes/generate', data);
    
    console.log("📥 API Service: Received response:", response.data);
    
    return response.data;
  },

  // Public: Get ALL generated recipes from ALL users
  async getAllGeneratedRecipes(page = 1, pageSize = 20) {
    const response = await api.get('/recipes/generated', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  // Authenticated: Get current user's history
  async getHistory(page = 1, pageSize = 10) {
    const response = await api.get('/recipes/history', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  // Public: Get any generated recipe by ID
  async getGeneratedRecipe(id: string): Promise<GeneratedRecipeResponse> {
    const response = await api.get(`/recipes/generated/${id}`);
    return response.data;
  },

  async toggleFavorite(recipeId: string) {
    const response = await api.patch(`/recipes/generated/${recipeId}/favorite`);
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