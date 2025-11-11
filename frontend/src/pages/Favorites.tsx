import { useState, useEffect } from "react";
import { Heart, ChefHat, Clock, Users, X } from "lucide-react";
import { recipeService } from "../lib/api/services/recepie.service";
import type { GeneratedRecipeResponse } from "../types/api.types";

type RecipeModalProps = {
  isOpen: boolean;
  onClose: () => void;
  recipe: GeneratedRecipeResponse | null;
};

const RecipeModal = ({ isOpen, onClose, recipe }: RecipeModalProps) => {
  if (!isOpen || !recipe) return null;

  return (
    <div className="fixed inset-0 flex justify-center items-center z-50 backdrop-blur-sm bg-black/30">
      <div className="bg-white/95 rounded-2xl shadow-xl w-11/12 max-w-2xl relative overflow-hidden h-[85vh] flex flex-col border border-gray-200">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition z-10"
        >
          <X size={20} className="text-gray-700" />
        </button>

        {/* Image */}
        {recipe.image_urls?.medium_url ? (
          <img
            src={recipe.image_urls.medium_url}
            alt={recipe.recipe.title}
            className="w-full h-56 object-cover"
          />
        ) : (
          <div className="w-full h-56 bg-gradient-to-br from-orange-200 to-red-200 flex items-center justify-center">
            <ChefHat className="w-20 h-20 text-orange-400" />
          </div>
        )}

        {/* Scrollable Content */}
        <div className="p-6 overflow-y-auto flex-1">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-3xl font-bold text-gray-800">
              {recipe.recipe.title}
            </h2>
          </div>

          {/* Recipe Info */}
          <div className="flex items-center space-x-4 mb-6 text-sm">
            <span className="flex items-center space-x-1 text-gray-600">
              <Clock className="w-4 h-4" />
              <span>{recipe.recipe.estimated_time} mins</span>
            </span>
            <span className="flex items-center space-x-1 text-gray-600">
              <Users className="w-4 h-4" />
              <span>{recipe.recipe.servings} servings</span>
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
              recipe.recipe.difficulty === "easy" ? "text-green-600 bg-green-50" :
              recipe.recipe.difficulty === "medium" ? "text-orange-600 bg-orange-50" :
              "text-red-600 bg-red-50"
            }`}>
              {recipe.recipe.difficulty}
            </span>
          </div>

          {/* Ingredients */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-3 flex items-center">
              <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
                Ingredients
              </span>
            </h3>
            <ul className="list-disc list-inside text-gray-600 space-y-1">
              {recipe.ingredients_used.map((item, index) => (
                <li key={index} className="capitalize">{item}</li>
              ))}
            </ul>
          </div>

          {/* Instructions */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-3 flex items-center">
              <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
                Instructions
              </span>
            </h3>
            <ol className="space-y-3">
              {recipe.recipe.steps.map((step, index) => (
                <li key={index} className="flex">
                  <span className="flex-shrink-0 w-7 h-7 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full flex items-center justify-center text-sm font-semibold mr-3">
                    {index + 1}
                  </span>
                  <span className="text-gray-600 pt-0.5">{step}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Tips */}
          {recipe.recipe.tips && (
            <div className="bg-orange-50 rounded-xl p-4 border border-orange-100">
              <h3 className="text-lg font-semibold text-orange-800 mb-2">
                💡 Chef's Tips
              </h3>
              <p className="text-orange-700 text-sm">{recipe.recipe.tips}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const FavoritesPage = () => {
  const [favoriteRecipes, setFavoriteRecipes] = useState<GeneratedRecipeResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecipe, setSelectedRecipe] = useState<GeneratedRecipeResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      const data = await recipeService.getFavorites(1, 50);
      setFavoriteRecipes(data.recipes || []);
    } catch (error) {
      console.error("Error fetching favorite recipes:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = async (recipeId: string) => {
    try {
      await recipeService.toggleFavorite(recipeId);
      // Remove from favorites list
      setFavoriteRecipes(favoriteRecipes.filter(recipe => recipe.id !== recipeId));
    } catch (error) {
      console.error("Error toggling favorite:", error);
    }
  };

  const handleViewRecipe = (recipe: GeneratedRecipeResponse) => {
    setSelectedRecipe(recipe);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setSelectedRecipe(null);
    setIsModalOpen(false);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy": return "text-green-600 bg-green-50";
      case "medium": return "text-orange-600 bg-orange-50";
      case "hard": return "text-red-600 bg-red-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  return (
    <div className="relative pt-20 min-h-screen bg-gradient-to-b from-orange-50 to-white">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-10 left-10 w-20 h-20 bg-orange-300 rounded-full blur-xl"></div>
        <div className="absolute top-40 right-20 w-32 h-32 bg-red-300 rounded-full blur-xl"></div>
        <div className="absolute bottom-20 left-1/3 w-24 h-24 bg-amber-300 rounded-full blur-xl"></div>
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="text-center mb-12 space-y-4">
          <h1 className="text-5xl font-bold flex items-center justify-center gap-3">
            <Heart className="text-red-500 fill-red-500" size={48} />
            <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
              Favorite Recipes
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your collection of beloved recipes
          </p>

          {/* Stats Bar */}
          {!loading && favoriteRecipes.length > 0 && (
            <div className="flex items-center justify-center space-x-8 pt-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{favoriteRecipes.length}</div>
                <div className="text-sm text-gray-500">Favorites</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {Math.round(favoriteRecipes.reduce((acc, r) => acc + r.recipe.estimated_time, 0) / favoriteRecipes.length) || 0}m
                </div>
                <div className="text-sm text-gray-500">Avg Cook Time</div>
              </div>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-orange-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-600">Loading your favorite recipes...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && favoriteRecipes.length === 0 && (
          <div className="text-center py-20">
            <Heart className="w-20 h-20 text-red-300 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-gray-700 mb-2">
              No favorite recipes yet
            </h3>
            <p className="text-gray-500 mb-6">
              Start adding recipes to your favorites to see them here!
            </p>
          </div>
        )}

        {/* Recipe Grid */}
        {!loading && favoriteRecipes.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {favoriteRecipes.map((recipe) => (
              <div
                key={recipe.id}
                className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transform hover:-translate-y-2 transition-all duration-300"
              >
                {/* Recipe Image */}
                <div className="relative h-48 bg-gradient-to-br from-orange-200 to-red-200 cursor-pointer"
                     onClick={() => handleViewRecipe(recipe)}>
                  {recipe.image_urls?.medium_url ? (
                    <img
                      src={recipe.image_urls.medium_url}
                      alt={recipe.recipe.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <ChefHat className="w-16 h-16 text-orange-400" />
                    </div>
                  )}
                  
                  {/* Favorite Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFavorite(recipe.id);
                    }}
                    className="absolute top-3 right-3 bg-white rounded-full p-2 shadow-lg hover:scale-110 transition-transform duration-200"
                  >
                    <Heart className="w-5 h-5 fill-red-500 text-red-500" />
                  </button>

                  {/* Difficulty Badge */}
                  <div className="absolute top-3 left-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getDifficultyColor(recipe.recipe.difficulty)}`}>
                      {recipe.recipe.difficulty}
                    </span>
                  </div>
                </div>

                {/* Recipe Content */}
                <div className="p-5 space-y-3">
                  <h3 className="text-xl font-bold text-gray-800 line-clamp-2 cursor-pointer hover:text-orange-600 transition-colors"
                      onClick={() => handleViewRecipe(recipe)}>
                    {recipe.recipe.title}
                  </h3>

                  {/* Ingredients Preview */}
                  <div className="flex flex-wrap gap-2">
                    {recipe.ingredients_used.slice(0, 3).map((ingredient, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-orange-50 text-orange-600 text-xs rounded-lg capitalize"
                      >
                        {ingredient}
                      </span>
                    ))}
                    {recipe.ingredients_used.length > 3 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-lg">
                        +{recipe.ingredients_used.length - 3} more
                      </span>
                    )}
                  </div>

                  {/* Recipe Info */}
                  <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                    <div className="flex items-center space-x-1 text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span className="text-sm">{recipe.recipe.estimated_time} mins</span>
                    </div>
                    <div className="flex items-center space-x-1 text-gray-600">
                      <Users className="w-4 h-4" />
                      <span className="text-sm">{recipe.recipe.servings} servings</span>
                    </div>
                  </div>

                  {/* View Recipe Button */}
                  <button
                    onClick={() => handleViewRecipe(recipe)}
                    className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-2 rounded-xl font-medium hover:from-orange-600 hover:to-red-600 transition-all duration-200"
                  >
                    View Recipe
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal Component */}
        <RecipeModal
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          recipe={selectedRecipe}
        />
      </div>
    </div>
  );
};

export default FavoritesPage;