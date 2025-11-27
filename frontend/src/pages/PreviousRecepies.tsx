import { useState, useEffect } from "react";
import { ChefHat, Clock, Search, Filter, Heart, X, Users, ChevronLeft, ChevronRight, Globe, Leaf } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { recipeService } from "../lib/api/services/recepie.service";
import type { GeneratedRecipeResponse, ImageUrls } from "../types/api.types";

type RecipeModalProps = {
  isOpen: boolean;
  onClose: () => void;
  recipe: GeneratedRecipeResponse | null;
};

const RecipeModal = ({ isOpen, onClose, recipe }: RecipeModalProps) => {
  const [expandedImageIndex, setExpandedImageIndex] = useState<number | null>(null);

  useEffect(() => {
    // Reset expanded image when modal opens with new recipe
    setExpandedImageIndex(null);
  }, [recipe?.id]);

  if (!isOpen || !recipe) return null;

  // Get all available image URLs
  let imageUrls: string[] = [];
  
  if (recipe.image_urls_list && recipe.image_urls_list.length > 0) {
    imageUrls = recipe.image_urls_list
      .map((img: ImageUrls) => img.medium_url || img.url)
      .filter(Boolean) as string[];
  } else if (recipe.image_urls) {
    imageUrls = [
      recipe.image_urls.medium_url || recipe.image_urls.url,
    ].filter(Boolean) as string[];
  }

  const hasImages = imageUrls.length > 0;

  const toggleImageExpand = (index: number) => {
    setExpandedImageIndex(expandedImageIndex === index ? null : index);
  };

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

        {/* Expandable Image Tiles Section */}
        {hasImages && (
          <div className="px-6 pt-6 pb-2">
            <div className="flex items-center gap-2 mb-3">
              <ChefHat className="w-5 h-5 text-orange-600" />
              <h3 className="text-sm font-semibold text-gray-700">
                Ingredient Images ({imageUrls.length})
              </h3>
            </div>
            <div className="space-y-2">
              {imageUrls.map((imageUrl, index) => (
                <div key={index} className="border border-gray-200 rounded-lg overflow-hidden bg-white">
                  {/* Collapsed Tile */}
                  <button
                    onClick={() => toggleImageExpand(index)}
                    className="w-full flex items-center gap-3 p-3 hover:bg-gray-50 transition-colors"
                  >
                    {/* Icon */}
                    <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-orange-100 to-red-100 rounded-lg flex items-center justify-center">
                      <ChefHat className="w-5 h-5 text-orange-600" />
                    </div>
                    
                    {/* File Info */}
                    <div className="flex-1 text-left">
                      <div className="text-sm font-medium text-gray-800">
                        Ingredient Image {index + 1}
                      </div>
                      <div className="text-xs text-gray-500">
                        Click to {expandedImageIndex === index ? 'collapse' : 'expand'}
                      </div>
                    </div>
                    
                    {/* Expand/Collapse Icon */}
                    <div className="flex-shrink-0">
                      {expandedImageIndex === index ? (
                        <ChevronLeft className="w-5 h-5 text-gray-400 rotate-90" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-400 rotate-90" />
                      )}
                    </div>
                  </button>
                  
                  {/* Expanded Image */}
                  {expandedImageIndex === index && (
                    <div className="border-t border-gray-200 p-3 bg-gray-50">
                      <img
                        src={imageUrl}
                        alt={`Ingredient ${index + 1}`}
                        className="w-full h-auto rounded-lg shadow-sm"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Scrollable Content */}
        <div className="p-6 overflow-y-auto flex-1">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-3xl font-bold text-gray-800">
              {recipe.recipe.title}
            </h2>
          </div>

          {/* Badges Row */}
          <div className="flex flex-wrap items-center gap-2 mb-6">
            {/* Difficulty Badge */}
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
              recipe.recipe.difficulty === "easy" ? "text-green-600 bg-green-50" :
              recipe.recipe.difficulty === "medium" ? "text-orange-600 bg-orange-50" :
              "text-red-600 bg-red-50"
            }`}>
              {recipe.recipe.difficulty}
            </span>

            {/* Cuisine Type Badge */}
            {(recipe.cuisine_type || recipe.options?.cuisine_type) && (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-600 flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {recipe.cuisine_type || recipe.options?.cuisine_type}
              </span>
            )}
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
          </div>

          {/* Dietary Preferences Section */}
          {(recipe.dietary_preferences || recipe.options?.dietary_preferences) && 
           (recipe.dietary_preferences?.length > 0 || recipe.options?.dietary_preferences?.length > 0) && (
            <div className="bg-green-50 rounded-xl p-4 border border-green-100 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Leaf className="w-5 h-5 text-green-600" />
                <h3 className="text-lg font-bold text-gray-800">Dietary Information</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {(recipe.dietary_preferences || recipe.options?.dietary_preferences || []).map((pref: string, index: number) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-white border border-green-200 text-green-700 rounded-full text-sm font-medium"
                  >
                    {pref}
                  </span>
                ))}
              </div>
            </div>
          )}

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

const BrowseRecipes = () => {
  const navigate = useNavigate();
  const [recipes, setRecipes] = useState<GeneratedRecipeResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("all");
  const [selectedTime, setSelectedTime] = useState<string>("all");
  const [selectedCuisine, setSelectedCuisine] = useState<string>("all");
  const [selectedRecipe, setSelectedRecipe] = useState<GeneratedRecipeResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchRecipes();
  }, []);

  const fetchRecipes = async () => {
    try {
      const data = await recipeService.getHistory(1, 50);
      setRecipes(data.recipes || []);
    } catch (error) {
      console.error("Error fetching recipes:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = async (recipeId: string) => {
    try {
      await recipeService.toggleFavorite(recipeId);
      
      setRecipes(recipes.map(recipe => 
        recipe.id === recipeId 
          ? { ...recipe, is_favorite: !recipe.is_favorite }
          : recipe
      ));
    } catch (error) {
      console.error("Error toggling favorite:", error);
    }
  };

  const openRecipeModal = (recipe: GeneratedRecipeResponse) => {
    setSelectedRecipe(recipe);
    setIsModalOpen(true);
  };

  // Get unique cuisines for filter
  const uniqueCuisines = Array.from(
    new Set(
      recipes
        .map(r => r.cuisine_type || r.options?.cuisine_type)
        .filter(Boolean)
    )
  ).sort();

  const filteredRecipes = recipes.filter(recipe => {
    const matchesSearch = recipe.recipe.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      recipe.ingredients_used.some(ing => ing.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesDifficulty = selectedDifficulty === "all" || recipe.recipe.difficulty === selectedDifficulty;
    
    const matchesTime = selectedTime === "all" || 
      (selectedTime === "quick" && recipe.recipe.estimated_time <= 30) ||
      (selectedTime === "medium" && recipe.recipe.estimated_time > 30 && recipe.recipe.estimated_time <= 60) ||
      (selectedTime === "long" && recipe.recipe.estimated_time > 60);

    const recipeCuisine = recipe.cuisine_type || recipe.options?.cuisine_type;
    const matchesCuisine = selectedCuisine === "all" || recipeCuisine === selectedCuisine;

    return matchesSearch && matchesDifficulty && matchesTime && matchesCuisine;
  });

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy": return "text-green-600 bg-green-50";
      case "medium": return "text-orange-600 bg-orange-50";
      case "hard": return "text-red-600 bg-red-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  // ✅ NEW: Helper function to get the primary image for recipe card
  const getPrimaryImageUrl = (recipe: GeneratedRecipeResponse): string | undefined => {
    if (recipe.image_urls_list && recipe.image_urls_list.length > 0) {
      return recipe.image_urls_list[0].medium_url || recipe.image_urls_list[0].url;
    }
    return recipe.image_urls?.medium_url || recipe.image_urls?.url;
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
          <h1 className="text-5xl font-bold">
            <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
              Browse Recipes
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Explore your AI-generated culinary creations
          </p>

          {/* Stats Bar */}
          <div className="flex items-center justify-center space-x-8 pt-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{recipes.length}</div>
              <div className="text-sm text-gray-500">Total Recipes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {recipes.filter(r => r.is_favorite).length}
              </div>
              <div className="text-sm text-gray-500">Favorites</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Math.round(recipes.reduce((acc, r) => acc + r.recipe.estimated_time, 0) / recipes.length) || 0}m
              </div>
              <div className="text-sm text-gray-500">Avg Cook Time</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search recipes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>

            {/* Cuisine Filter */}
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={selectedCuisine}
                onChange={(e) => setSelectedCuisine(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 appearance-none bg-white"
              >
                <option value="all">All Cuisines</option>
                {uniqueCuisines.map((cuisine) => (
                  <option key={cuisine} value={cuisine}>
                    {cuisine}
                  </option>
                ))}
              </select>
            </div>

            {/* Difficulty Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 appearance-none bg-white"
              >
                <option value="all">All Difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            {/* Time Filter */}
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={selectedTime}
                onChange={(e) => setSelectedTime(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 appearance-none bg-white"
              >
                <option value="all">All Times</option>
                <option value="quick">Quick (≤30 min)</option>
                <option value="medium">Medium (30-60 min)</option>
                <option value="long">Long (&gt;60 min)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-orange-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-600">Loading delicious recipes...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredRecipes.length === 0 && (
          <div className="text-center py-20">
            <ChefHat className="w-20 h-20 text-gray-300 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-gray-700 mb-2">No recipes found</h3>
            <p className="text-gray-500 mb-6">
              {recipes.length === 0 
                ? "Start creating some amazing recipes!" 
                : "Try adjusting your filters"}
            </p>
            <button
              onClick={() => navigate("/upload")}
              className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-3 rounded-xl font-semibold hover:from-orange-600 hover:to-red-600 transform hover:scale-105 transition-all duration-200 shadow-xl"
            >
              Create Your First Recipe
            </button>
          </div>
        )}

        {/* Recipe Grid */}
        {!loading && filteredRecipes.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRecipes.map((recipe) => {
              const cuisineType = recipe.cuisine_type || recipe.options?.cuisine_type;
              const dietaryPrefs = recipe.dietary_preferences || recipe.options?.dietary_preferences || [];
              const primaryImageUrl = getPrimaryImageUrl(recipe);
              const hasMultipleImages = recipe.image_urls_list && recipe.image_urls_list.length > 1;
              
              return (
                <div
                  key={recipe.id}
                  onClick={() => openRecipeModal(recipe)}
                  className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transform hover:-translate-y-2 transition-all duration-300 cursor-pointer"
                >
                  {/* Recipe Image */}
                  <div className="relative h-48 bg-gradient-to-br from-orange-200 to-red-200">
                    {primaryImageUrl ? (
                      <img
                        src={primaryImageUrl}
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
                      <Heart
                        className={`w-5 h-5 ${
                          recipe.is_favorite
                            ? "fill-red-500 text-red-500"
                            : "text-gray-400"
                        }`}
                      />
                    </button>

                    {/* Difficulty Badge */}
                    <div className="absolute top-3 left-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getDifficultyColor(recipe.recipe.difficulty)}`}>
                        {recipe.recipe.difficulty}
                      </span>
                    </div>

                    {/* ✅ NEW: Multiple Images Indicator */}
                    {hasMultipleImages && (
                      <div className="absolute top-12 left-3">
                        <span className="px-2 py-1 bg-black/70 text-white text-xs rounded-full flex items-center gap-1">
                          📸 {recipe.image_urls_list!.length}
                        </span>
                      </div>
                    )}

                    {/* Cuisine Badge */}
                    {cuisineType && (
                      <div className="absolute bottom-3 left-3">
                        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-600 flex items-center gap-1">
                          <Globe className="w-3 h-3" />
                          {cuisineType}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Recipe Content */}
                  <div className="p-5 space-y-3">
                    <h3 className="text-xl font-bold text-gray-800 line-clamp-2">
                      {recipe.recipe.title}
                    </h3>

                    {/* Dietary Preferences Pills */}
                    {dietaryPrefs.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {dietaryPrefs.slice(0, 2).map((pref: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-green-50 text-green-600 text-xs rounded-lg flex items-center gap-1"
                          >
                            <Leaf className="w-3 h-3" />
                            {pref}
                          </span>
                        ))}
                        {dietaryPrefs.length > 2 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-lg">
                            +{dietaryPrefs.length - 2}
                          </span>
                        )}
                      </div>
                    )}

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
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Recipe Modal */}
      <RecipeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        recipe={selectedRecipe}
      />
    </div>
  );
};

export default BrowseRecipes;