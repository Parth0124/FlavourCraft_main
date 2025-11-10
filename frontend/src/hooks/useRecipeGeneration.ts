import { useState } from 'react';
import { recipeService } from '../lib/api/services/recepie.service';
import type { 
  RecipeGenerationRequest, 
  GeneratedRecipeResponse,
  RecipeHistoryResponse,
  ImageUrls 
} from '../types/api.types';

export function useRecipeGeneration() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedRecipe, setGeneratedRecipe] = useState<GeneratedRecipeResponse | null>(null);
  const [recipeHistory, setRecipeHistory] = useState<RecipeHistoryResponse | null>(null);
  const [favorites, setFavorites] = useState<RecipeHistoryResponse | null>(null);

  /**
   * Generate a recipe from ingredients
   * Now supports including image URLs from the upload step
   */
  const generateRecipe = async (
    ingredients: string[],
    options?: {
      dietary_preferences?: string[];
      cuisine_type?: string;
      cooking_time?: number;
      difficulty?: 'easy' | 'medium' | 'hard';
      image_urls?: ImageUrls;  // Include ingredient image URLs
    }
  ): Promise<GeneratedRecipeResponse> => {
    setLoading(true);
    setError(null);
    
    try {
      // Build request object, only including fields that have values
      const data: RecipeGenerationRequest = {
        ingredients: ingredients.filter(i => i && i.trim()) // Remove empty ingredients
      };

      // Only add optional fields if they have actual values
      if (options?.dietary_preferences && options.dietary_preferences.length > 0) {
        data.dietary_preferences = options.dietary_preferences;
      }
      
      if (options?.cuisine_type && options.cuisine_type.trim()) {
        data.cuisine_type = options.cuisine_type;
      }
      
      if (options?.cooking_time && options.cooking_time > 0) {
        data.cooking_time = options.cooking_time;
      }
      
      if (options?.difficulty) {
        data.difficulty = options.difficulty;
      }
      
      if (options?.image_urls) {
        data.image_urls = options.image_urls;
      }

      console.log('useRecipeGeneration - sending data:', data);

      const recipe = await recipeService.generateRecipe(data);
      setGeneratedRecipe(recipe);
      
      return recipe;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to generate recipe';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get recipe generation history
   * Returns recipes with their ingredient images
   */
  const getHistory = async (page = 1, pageSize = 10) => {
    setLoading(true);
    setError(null);
    
    try {
      const history = await recipeService.getHistory(page, pageSize);
      setRecipeHistory(history);
      return history;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch history');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Get a specific recipe by ID
   */
  const getRecipeById = async (id: string): Promise<GeneratedRecipeResponse> => {
    setLoading(true);
    setError(null);
    
    try {
      const recipe = await recipeService.getGeneratedRecipe(id);
      setGeneratedRecipe(recipe);
      return recipe;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch recipe');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Toggle favorite status of a recipe
   */
  const toggleFavorite = async (recipeId: string) => {
    try {
      await recipeService.toggleFavorite(recipeId);
      
      // Update local state if recipe is currently loaded
      if (generatedRecipe && generatedRecipe.id === recipeId) {
        setGeneratedRecipe({
          ...generatedRecipe,
          is_favorite: !generatedRecipe.is_favorite
        });
      }
      
      // Refresh history if loaded
      if (recipeHistory) {
        const updatedRecipes = recipeHistory.recipes.map(recipe =>
          recipe.id === recipeId
            ? { ...recipe, is_favorite: !recipe.is_favorite }
            : recipe
        );
        setRecipeHistory({ ...recipeHistory, recipes: updatedRecipes });
      }
      
      return true;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to toggle favorite');
      throw err;
    }
  };

  /**
   * Get favorite recipes
   */
  const getFavorites = async (page = 1, pageSize = 10) => {
    setLoading(true);
    setError(null);
    
    try {
      const favs = await recipeService.getFavorites(page, pageSize);
      setFavorites(favs);
      return favs;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch favorites');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Reset all state
   */
  const reset = () => {
    setGeneratedRecipe(null);
    setRecipeHistory(null);
    setFavorites(null);
    setError(null);
  };

  return {
    // Main functions
    generateRecipe,
    getHistory,
    getRecipeById,
    toggleFavorite,
    getFavorites,
    reset,
    
    // State
    generatedRecipe,
    recipeHistory,
    favorites,
    loading,
    error
  };
}