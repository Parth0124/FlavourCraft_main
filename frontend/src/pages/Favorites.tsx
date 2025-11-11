import { useState, useEffect } from "react";
import { Heart, Loader2 } from "lucide-react";
import RecipeModal from "@/components/Modal";
import { recipeService } from "../lib/api/services/recepie.service";
import type { GeneratedRecipeResponse } from "@/types/api.types";

const FavoritesPage = () => {
  const [favoriteRecipes, setFavoriteRecipes] = useState<TransformedRecipe[]>([]);
  const [selectedRecipe, setSelectedRecipe] = useState<TransformedRecipe | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  type TransformedRecipe = {
    id: string;
    title: string;
    image: string;
    description: string;
    ingredients: string[];
    instructions: string;
    difficulty: string;
    estimatedTime: number;
    servings: number;
    tips?: string;
    createdAt: string;
    username?: string;
  };

  // Transform API response to component format
  const transformRecipe = (apiRecipe: GeneratedRecipeResponse): TransformedRecipe => {
    return {
      id: apiRecipe.id,
      title: apiRecipe.recipe.title,
      image: apiRecipe.image_urls?.medium_url || apiRecipe.image_urls?.url || '/placeholder-recipe.jpg',
      description: apiRecipe.recipe.tips || `A delicious ${apiRecipe.recipe.difficulty} recipe that takes approximately ${apiRecipe.recipe.estimated_time} minutes to prepare.`,
      ingredients: apiRecipe.ingredients_used,
      instructions: apiRecipe.recipe.steps.map((step, index) => `${index + 1}. ${step}`).join('\n'),
      difficulty: apiRecipe.recipe.difficulty,
      estimatedTime: apiRecipe.recipe.estimated_time,
      servings: apiRecipe.recipe.servings,
      tips: apiRecipe.recipe.tips,
      createdAt: apiRecipe.created_at,
      username: apiRecipe.username
    };
  };

  // Fetch favorite recipes
  const fetchFavorites = async (pageNum: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await recipeService.getFavorites(pageNum, 10);
      
      const transformedRecipes = response.recipes.map(transformRecipe);
      
      if (pageNum === 1) {
        setFavoriteRecipes(transformedRecipes);
      } else {
        setFavoriteRecipes(prev => [...prev, ...transformedRecipes]);
      }
      
      setHasMore(response.recipes.length === response.page_size);
      
    } catch (err: any) {
      console.error("Error fetching favorites:", err);
      setError(err.response?.data?.detail || "Failed to load favorite recipes");
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchFavorites(1);
  }, []);

  // Load more
  const loadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    fetchFavorites(nextPage);
  };

  const handleViewRecipe = (recipe: TransformedRecipe) => {
    setSelectedRecipe(recipe);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setSelectedRecipe(null);
    setIsModalOpen(false);
  };

  // Loading state
  if (loading && page === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-orange-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading your favorite recipes...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && page === 1) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white flex items-center justify-center">
        <div className="text-center">
          <Heart className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Oops!</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => fetchFavorites(1)}
            className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-2 rounded-xl font-medium transition-all duration-200"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8 mt-20">
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
            <Heart className="text-red-500" />
            My Favorite Recipes
          </h1>
          <div className="text-sm text-gray-600">
            {favoriteRecipes.length} {favoriteRecipes.length === 1 ? 'recipe' : 'recipes'}
          </div>
        </div>

        {favoriteRecipes.length > 0 ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {favoriteRecipes.map((recipe) => (
                <div
                  key={recipe.id}
                  className="bg-white rounded-2xl shadow-md hover:shadow-lg transition-shadow duration-300"
                >
                  <img
                    src={recipe.image}
                    alt={recipe.title}
                    className="w-full h-48 object-cover rounded-t-2xl"
                    onError={(e) => {
                      e.currentTarget.src = '/placeholder-recipe.jpg';
                    }}
                  />
                  <div className="p-4">
                    <h2 className="text-xl font-semibold mb-2 text-gray-800">
                      {recipe.title}
                    </h2>
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-2">
                      <span className="flex items-center gap-1">
                        ⏱️ {recipe.estimatedTime} min
                      </span>
                      <span className="capitalize">
                        📊 {recipe.difficulty}
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                      {recipe.description}
                    </p>
                    {recipe.username && (
                      <p className="text-xs text-gray-400 mb-3">
                        by {recipe.username}
                      </p>
                    )}
                    <button
                      onClick={() => handleViewRecipe(recipe)}
                      className="w-full bg-orange-500 hover:bg-orange-600 text-white py-2 rounded-xl font-medium transition-all duration-200"
                    >
                      View Recipe
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Load More Button */}
            {hasMore && (
              <div className="text-center mt-8">
                <button
                  onClick={loadMore}
                  disabled={loading}
                  className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3 rounded-xl font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    'Load More'
                  )}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center text-gray-600 mt-20">
            <Heart className="mx-auto text-red-400 mb-4" size={64} />
            <p className="text-xl mb-2">No favorite recipes yet</p>
            <p className="text-gray-500 mb-6">
              Start generating recipes and mark them as favorites!
            </p>
            <button
              onClick={() => window.location.href = '/generate'}
              className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200"
            >
              Generate a Recipe
            </button>
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