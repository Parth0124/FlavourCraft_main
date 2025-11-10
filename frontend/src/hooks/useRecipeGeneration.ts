import { useState } from 'react';
import { recipeService } from '../lib/api/services/recepie.service';
import type { RecipeGenerationRequest, GeneratedRecipeResponse } from '@/types/api.types';

export function useRecipeGeneration() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedRecipe, setGeneratedRecipe] = useState<GeneratedRecipeResponse | null>(null);

  const generateRecipe = async (data: RecipeGenerationRequest) => {
    setLoading(true);
    setError(null);
    try {
      const recipe = await recipeService.generateRecipe(data);
      setGeneratedRecipe(recipe);
      return recipe;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate recipe');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setGeneratedRecipe(null);
    setError(null);
  };

  return {
    generateRecipe,
    generatedRecipe,
    loading,
    error,
    reset
  };
}