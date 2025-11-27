import { useState, useEffect } from "react";
import { 
  ChefHat, 
  Clock, 
  Users, 
  TrendingUp, 
  Sparkles, 
  Check,
  X,
  Plus,
  Lightbulb,
  Heart,
  HeartOff
} from "lucide-react";
import { useRecipeGeneration } from "@/hooks/useRecipeGeneration";
import { toast } from "react-hot-toast";
import type { ImageUrls, GeneratedRecipeResponse } from "@/types/api.types";

interface RecipeGeneratorProps {
  ingredientCount?: number;  // Optional, not used but kept for backward compatibility
  detectedIngredients: string[];
  imageUrls?: ImageUrls;
}

const RecipeGenerator: React.FC<RecipeGeneratorProps> = ({
  detectedIngredients = [],
  imageUrls
}) => {
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [newIngredient, setNewIngredient] = useState("");
  const [cuisineType, setCuisineType] = useState("");
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard" | "">("");
  const [cookingTime, setCookingTime] = useState<number | "">("");
  const [dietaryPreferencesText, setDietaryPreferencesText] = useState("");
  const [recipe, setRecipe] = useState<GeneratedRecipeResponse | null>(null);

  const { generateRecipe, toggleFavorite, loading, error } = useRecipeGeneration();

  // Initialize with detected ingredients
  useEffect(() => {
    if (detectedIngredients && detectedIngredients.length > 0) {
      setIngredients(detectedIngredients);
    }
  }, [detectedIngredients]);

  // Debug: Log when imageUrls prop changes
  useEffect(() => {
    console.log("📸 RecipeGenerator received imageUrls:", imageUrls);
  }, [imageUrls]);

  // Add ingredient
  const addIngredient = () => {
    if (newIngredient.trim() && !ingredients.includes(newIngredient.trim())) {
      setIngredients([...ingredients, newIngredient.trim()]);
      setNewIngredient("");
      toast.success(`Added: ${newIngredient.trim()}`);
    }
  };

  // Remove ingredient
  const removeIngredient = (ingredient: string) => {
    setIngredients(ingredients.filter(i => i !== ingredient));
    toast.success(`Removed: ${ingredient}`);
  };

  // Generate the recipe with image URLs
  const handleGenerateRecipe = async () => {
    if (ingredients.length === 0) {
      toast.error("Please add at least one ingredient");
      return;
    }

    const toastId = toast.loading("Generating your recipe...");

    try {
      console.log("🚀 RecipeGenerator - Starting generation");
      console.log("   Ingredients:", ingredients);
      console.log("   Image URLs prop:", imageUrls);
      
      // Build options object
      const options: any = {};
      
      // Add cuisine type if provided
      if (cuisineType && cuisineType.trim()) {
        options.cuisine_type = cuisineType.trim();
      }
      
      // Add difficulty if selected
      if (difficulty) {
        options.difficulty = difficulty.toLowerCase() as 'easy' | 'medium' | 'hard';
      }
      
      // Add cooking time if provided
      if (cookingTime && Number(cookingTime) > 0) {
        options.cooking_time = Number(cookingTime);
      }
      
      // ✅ Parse comma-separated dietary preferences
      if (dietaryPreferencesText && dietaryPreferencesText.trim()) {
        const preferences = dietaryPreferencesText
          .split(',')
          .map(p => p.trim())
          .filter(p => p.length > 0);
        
        if (preferences.length > 0) {
          options.dietary_preferences = preferences;
          console.log("   ✅ Parsed dietary preferences:", preferences);
        }
      }

      // ✅ Add image URLs to options if available
      if (imageUrls) {
        options.image_urls = imageUrls;
        console.log("   ✅ Including image URLs in options:", imageUrls);
      } else {
        console.warn("   ⚠️  No image URLs available to include");
      }

      console.log("📤 RecipeGenerator - Calling generateRecipe with:");
      console.log("   Ingredients:", ingredients);
      console.log("   Options:", options);

      // Call hook with ingredients and options
      const generatedRecipe = await generateRecipe(ingredients, options);

      console.log("📥 RecipeGenerator - Recipe generated:", generatedRecipe);
      console.log("   Recipe ID:", generatedRecipe.id);
      console.log("   Image URLs in response:", generatedRecipe.image_urls);

      setRecipe(generatedRecipe);
      toast.success("Recipe generated successfully!", { id: toastId });
    } catch (err: any) {
      console.error("❌ RecipeGenerator - Generation error:", err);
      console.error("   Error response:", err.response?.data);
      
      // Extract error message
      let errorMsg = "Failed to generate recipe";
      if (err.response?.data) {
        const data = err.response.data;
        if (typeof data.detail === 'string') {
          errorMsg = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorMsg = data.detail.map((e: any) => {
            if (e.msg && e.loc) {
              return `${e.loc.join('.')}: ${e.msg}`;
            }
            return e.msg || JSON.stringify(e);
          }).join('; ');
        } else if (data.message) {
          errorMsg = data.message;
        } else {
          errorMsg = JSON.stringify(data.detail || data);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      toast.error(errorMsg, { id: toastId });
    }
  };

  // Toggle favorite
  const handleToggleFavorite = async () => {
    if (!recipe) return;

    try {
      await toggleFavorite(recipe.id);
      setRecipe({ ...recipe, is_favorite: !recipe.is_favorite });
      toast.success(recipe.is_favorite ? "Removed from favorites" : "Added to favorites");
    } catch (err) {
      toast.error("Failed to update favorite status");
    }
  };

  // Reset form
  const resetForm = () => {
    setRecipe(null);
    setCuisineType("");
    setDifficulty("");
    setCookingTime("");
    setDietaryPreferencesText("");
  };

  // If recipe is generated, show the recipe
  if (recipe) {
    return (
      <div className="h-full overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
            <ChefHat className="w-8 h-8 text-orange-500" />
            {recipe.recipe.title}
          </h2>
          <div className="flex gap-2">
            <button
              onClick={handleToggleFavorite}
              className="p-2 rounded-full hover:bg-orange-100 transition-colors"
            >
              {recipe.is_favorite ? (
                <Heart className="w-6 h-6 text-red-500 fill-current" />
              ) : (
                <HeartOff className="w-6 h-6 text-gray-400" />
              )}
            </button>
            <button
              onClick={resetForm}
              className="px-4 py-2 bg-white border-2 border-orange-300 text-orange-600 rounded-xl hover:bg-orange-50 transition-all"
            >
              New Recipe
            </button>
          </div>
        </div>

        {/* Ingredient Image */}
        {recipe.image_urls && (
          <div className="mb-6 rounded-xl overflow-hidden shadow-lg">
            <img 
              src={recipe.image_urls.medium_url} 
              alt="Ingredients" 
              className="w-full h-48 object-cover"
              onError={(e) => {
                console.error("❌ Failed to load image:", recipe.image_urls?.medium_url);
                e.currentTarget.style.display = 'none';
              }}
              onLoad={() => {
                console.log("✅ Image loaded successfully:", recipe.image_urls?.medium_url);
              }}
            />
            <div className="bg-white p-2 text-xs text-gray-500 text-center">
              Your ingredients
            </div>
          </div>
        )}

        {/* Recipe Meta */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 text-center shadow-md">
            <Clock className="w-6 h-6 text-orange-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Time</p>
            <p className="text-lg font-bold text-gray-800">{recipe.recipe.estimated_time} min</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-md">
            <TrendingUp className="w-6 h-6 text-orange-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Difficulty</p>
            <p className="text-lg font-bold text-gray-800 capitalize">{recipe.recipe.difficulty}</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-md">
            <Users className="w-6 h-6 text-orange-500 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Servings</p>
            <p className="text-lg font-bold text-gray-800">{recipe.recipe.servings}</p>
          </div>
        </div>

        {/* Ingredients Used */}
        <div className="bg-white rounded-xl p-4 mb-6 shadow-md">
          <h3 className="text-lg font-bold text-gray-800 mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-orange-500" />
            Ingredients
          </h3>
          <div className="flex flex-wrap gap-2">
            {recipe.ingredients_used.map((ing, idx) => (
              <span 
                key={idx}
                className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium"
              >
                {ing}
              </span>
            ))}
          </div>
        </div>

        {/* Steps */}
        <div className="bg-white rounded-xl p-4 mb-6 shadow-md">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <ChefHat className="w-5 h-5 text-orange-500" />
            Instructions
          </h3>
          <ol className="space-y-3">
            {recipe.recipe.steps.map((step, idx) => (
              <li key={idx} className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-gradient-to-r from-orange-300 to-red-900 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {idx + 1}
                </span>
                <p className="text-gray-700 flex-1">{step}</p>
              </li>
            ))}
          </ol>
        </div>

        {/* Tips */}
        {recipe.recipe.tips && (
          <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-xl p-4 shadow-md">
            <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-orange-500" />
              Chef's Tips
            </h3>
            <p className="text-gray-700">{recipe.recipe.tips}</p>
          </div>
        )}
      </div>
    );
  }

  // Recipe generation form
  return (
    <div className="h-full overflow-y-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <ChefHat className="w-7 h-7 text-orange-500" />
        Customize Your Recipe
      </h2>

      {/* Image URL status */}
      {imageUrls && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-xs">
          <p className="text-green-800 font-medium">✅ Image ready for recipe</p>
          <p className="text-green-600 mt-1 truncate">URL: {imageUrls.medium_url}</p>
        </div>
      )}

      {!imageUrls && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs">
          <p className="text-blue-800 font-medium">ℹ️ No ingredient image attached</p>
          <p className="text-blue-600 mt-1">Recipe will be generated without image</p>
        </div>
      )}

      {/* Ingredients Section */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Ingredients ({ingredients.length})
        </label>
        
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={newIngredient}
            onChange={(e) => setNewIngredient(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addIngredient()}
            placeholder="Add ingredient..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
          <button
            onClick={addIngredient}
            className="px-4 py-2 bg-gradient-to-r from-orange-300 to-red-900 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 bg-gray-50 rounded-xl">
          {ingredients.map((ing, idx) => (
            <span 
              key={idx}
              className="inline-flex items-center gap-1 px-3 py-1 bg-white border border-gray-300 rounded-full text-sm group hover:border-red-300 transition-colors"
            >
              <Check className="w-3 h-3 text-green-500" />
              {ing}
              <button
                onClick={() => removeIngredient(ing)}
                className="ml-1 text-gray-400 hover:text-red-500 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* ✅ CHANGED: Cuisine Type - Text Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Cuisine Type (Optional)
        </label>
        <input
          type="text"
          value={cuisineType}
          onChange={(e) => setCuisineType(e.target.value)}
          placeholder="e.g., Italian, Mexican, Indian, Thai"
          className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">
          Enter any cuisine type you prefer
        </p>
      </div>

      {/* Difficulty */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Difficulty Level (Optional)
        </label>
        <div className="flex gap-2">
          {["easy", "medium", "hard"].map((level) => (
            <button
              key={level}
              onClick={() => setDifficulty(level as any)}
              className={`flex-1 py-2 px-4 rounded-xl font-medium transition-all ${
                difficulty === level
                  ? "bg-gradient-to-r from-orange-300 to-red-900 text-white"
                  : "bg-white border border-gray-300 text-gray-700 hover:border-orange-300"
              }`}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Cooking Time */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Max Cooking Time (Optional)
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={cookingTime}
            onChange={(e) => setCookingTime(e.target.value ? Number(e.target.value) : "")}
            placeholder="Minutes"
            min="1"
            max="180"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
          <span className="text-gray-600">minutes</span>
        </div>
      </div>

      {/* ✅ CHANGED: Dietary Preferences - Text Input with comma separation */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Dietary Preferences (Optional)
        </label>
        <input
          type="text"
          value={dietaryPreferencesText}
          onChange={(e) => setDietaryPreferencesText(e.target.value)}
          placeholder="e.g., Vegetarian, Vegan, Gluten-Free, Dairy-Free"
          className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">
          Separate multiple preferences with commas
        </p>
        
        {/* Preview of parsed preferences */}
        {dietaryPreferencesText && dietaryPreferencesText.trim() && (
          <div className="mt-2 flex flex-wrap gap-2">
            {dietaryPreferencesText
              .split(',')
              .map(p => p.trim())
              .filter(p => p.length > 0)
              .map((pref, idx) => (
                <span 
                  key={idx}
                  className="px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs"
                >
                  {pref}
                </span>
              ))}
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerateRecipe}
        disabled={loading || ingredients.length === 0}
        className={`w-full py-4 rounded-xl font-bold text-lg transition-all duration-200 flex items-center justify-center gap-2 ${
          loading || ingredients.length === 0
            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
            : "bg-gradient-to-r from-orange-300 to-red-900 text-white hover:from-orange-600 hover:to-red-600 transform hover:scale-105 shadow-lg"
        }`}
      >
        <Sparkles className={`w-6 h-6 ${loading ? 'animate-spin' : ''}`} />
        {loading ? "Generating..." : "Generate Recipe"}
      </button>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          {typeof error === 'string' ? error : 'An error occurred'}
        </div>
      )}
    </div>
  );
};

export default RecipeGenerator;