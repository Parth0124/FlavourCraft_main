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
      console.log('🚀 useRecipeGeneration - Starting recipe generation');
      console.log('   Ingredients:', ingredients);
      console.log('   Options:', options);
      
      // Validate ingredients
      const validIngredients = ingredients.filter(i => i && i.trim());
      if (validIngredients.length === 0) {
        throw new Error('At least one ingredient is required');
      }
      
      // Build request object, only including fields that have values
      const data: RecipeGenerationRequest = {
        ingredients: validIngredients
      };

      // Only add optional fields if they have actual values
      if (options?.dietary_preferences && options.dietary_preferences.length > 0) {
        data.dietary_preferences = options.dietary_preferences;
        console.log('   ✅ Added dietary preferences:', options.dietary_preferences);
      }
      
      if (options?.cuisine_type && options.cuisine_type.trim()) {
        data.cuisine_type = options.cuisine_type;
        console.log('   ✅ Added cuisine type:', options.cuisine_type);
      }
      
      if (options?.cooking_time && options.cooking_time > 0) {
        data.cooking_time = options.cooking_time;
        console.log('   ✅ Added cooking time:', options.cooking_time);
      }
      
      if (options?.difficulty) {
        data.difficulty = options.difficulty;
        console.log('   ✅ Added difficulty:', options.difficulty);
      }
      
      // ✅ CRITICAL: Validate and add image URLs
      if (options?.image_urls) {
        // Validate image URLs structure
        if (options.image_urls.url && 
            options.image_urls.medium_url && 
            options.image_urls.thumbnail_url &&
            options.image_urls.public_id) {
          data.image_urls = options.image_urls;
          console.log('   ✅ Added image URLs:', {
            url: options.image_urls.url,
            medium_url: options.image_urls.medium_url,
            thumbnail_url: options.image_urls.thumbnail_url,
            public_id: options.image_urls.public_id
          });
        } else {
          console.warn('   ⚠️  Image URLs incomplete, skipping:', options.image_urls);
        }
      } else {
        console.log('   ℹ️  No image URLs provided');
      }

      console.log('📤 useRecipeGeneration - Final request data:', JSON.stringify(data, null, 2));

      // Call API service
      const recipe = await recipeService.generateRecipe(data);
      
      console.log('📥 useRecipeGeneration - Recipe generated successfully');
      console.log('   Recipe ID:', recipe.id);
      console.log('   Recipe title:', recipe.recipe.title);
      console.log('   Has image URLs in response:', !!recipe.image_urls);
      
      if (recipe.image_urls) {
        console.log('   ✅ Image URLs in response:', {
          url: recipe.image_urls.url,
          medium_url: recipe.image_urls.medium_url,
          thumbnail_url: recipe.image_urls.thumbnail_url
        });
      } else {
        console.warn('   ⚠️  No image URLs in response - check backend');
      }
      
      setGeneratedRecipe(recipe);
      
      return recipe;
    } catch (err: any) {
      console.error('❌ useRecipeGeneration - Error:', err);
      console.error('   Error response:', err.response?.data);
      
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate recipe';
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
      console.log(`📚 Fetching recipe history (page ${page}, size ${pageSize})`);
      
      const history = await recipeService.getHistory(page, pageSize);
      
      console.log(`✅ Fetched ${history.recipes.length} recipes`);
      console.log(`   Recipes with images: ${history.recipes.filter((r: GeneratedRecipeResponse) => r.image_urls).length}`);
      
      setRecipeHistory(history);
      return history;
    } catch (err: any) {
      console.error('❌ Failed to fetch history:', err);
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
      console.log(`🔍 Fetching recipe by ID: ${id}`);
      
      const recipe = await recipeService.getGeneratedRecipe(id);
      
      console.log(`✅ Recipe fetched: ${recipe.recipe.title}`);
      console.log(`   Has image URLs: ${!!recipe.image_urls}`);
      
      setGeneratedRecipe(recipe);
      return recipe;
    } catch (err: any) {
      console.error('❌ Failed to fetch recipe:', err);
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
      console.log(`⭐ Toggling favorite for recipe: ${recipeId}`);
      
      await recipeService.toggleFavorite(recipeId);
      
      console.log('✅ Favorite toggled successfully');
      
      // Update local state if recipe is currently loaded
      if (generatedRecipe && generatedRecipe.id === recipeId) {
        setGeneratedRecipe({
          ...generatedRecipe,
          is_favorite: !generatedRecipe.is_favorite
        });
      }
      
      // Refresh history if loaded
      if (recipeHistory) {
        const updatedRecipes = recipeHistory.recipes.map((recipe: GeneratedRecipeResponse) =>
          recipe.id === recipeId
            ? { ...recipe, is_favorite: !recipe.is_favorite }
            : recipe
        );
        setRecipeHistory({ ...recipeHistory, recipes: updatedRecipes });
      }

      // Refresh favorites if loaded
      if (favorites) {
        const updatedFavorites = favorites.recipes.map((recipe: GeneratedRecipeResponse) =>
          recipe.id === recipeId
            ? { ...recipe, is_favorite: !recipe.is_favorite }
            : recipe
        );
        setFavorites({ ...favorites, recipes: updatedFavorites });
      }
      
      return true;
    } catch (err: any) {
      console.error('❌ Failed to toggle favorite:', err);
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
      console.log(`⭐ Fetching favorite recipes (page ${page}, size ${pageSize})`);
      
      const favs = await recipeService.getFavorites(page, pageSize);
      
      console.log(`✅ Fetched ${favs.recipes.length} favorite recipes`);
      
      setFavorites(favs);
      return favs;
    } catch (err: any) {
      console.error('❌ Failed to fetch favorites:', err);
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
    console.log('🔄 Resetting recipe generation state');
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