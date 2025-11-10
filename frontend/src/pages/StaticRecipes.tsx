import { useState, useEffect } from "react";
import { Search, Filter, Clock, Users, ChefHat, X, Loader2 } from "lucide-react";
import { recipeService } from "../lib/api/services/recepie.service";
import type { StaticRecipe } from "../types/api.types";
import RecipeModal from "../components/Modal";

const StaticRecipes = () => {
  const [recipes, setRecipes] = useState<StaticRecipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalRecipes, setTotalRecipes] = useState(0);
  const [pageSize] = useState(20);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [maxPrepTime, setMaxPrepTime] = useState<string>("");
  const [maxCookTime, setMaxCookTime] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);
  
  // Modal
  const [selectedRecipe, setSelectedRecipe] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const availableTags = [
    "vegetarian",
    "vegan",
    "gluten-free",
    "dairy-free",
    "indian",
    "italian",
    "chinese",
    "mexican",
    "japanese",
    "thai",
    "mediterranean",
    "french",
    "appetizer",
    "main-course",
    "dessert",
    "breakfast",
    "lunch",
    "dinner",
    "snack",
    "soup",
    "salad",
  ];

  const difficulties = ["easy", "medium", "hard"];

  // Fetch recipes
  const fetchRecipes = async () => {
    setLoading(true);
    setError(null);

    try {
      // Check if any filters are applied
      const hasFilters =
        searchQuery ||
        selectedDifficulty ||
        selectedTags.length > 0 ||
        maxPrepTime ||
        maxCookTime;

      if (hasFilters) {
        // Use search endpoint with filters
        const params: any = {
          page,
          page_size: pageSize,
        };

        if (searchQuery) {
          params.ingredients = searchQuery;
        }
        if (selectedDifficulty) {
          params.difficulty = selectedDifficulty;
        }
        if (selectedTags.length > 0) {
          params.tags = selectedTags.join(",");
        }
        if (maxPrepTime) {
          params.max_prep_time = parseInt(maxPrepTime);
        }
        if (maxCookTime) {
          params.max_cook_time = parseInt(maxCookTime);
        }

        const response = await recipeService.searchStaticRecipes(params);
        setRecipes(response.recipes);
        setTotalRecipes(response.total);
      } else {
        // Use regular get all endpoint
        const response = await recipeService.getStaticRecipes(page, pageSize);
        setRecipes(response.recipes);
        setTotalRecipes(response.total);
      }
    } catch (err: any) {
      console.error("Error fetching recipes:", err);
      setError(err.response?.data?.detail || "Failed to load recipes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, [page]);

  const handleSearch = () => {
    setPage(1); // Reset to first page when searching
    fetchRecipes();
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setSelectedDifficulty("");
    setSelectedTags([]);
    setMaxPrepTime("");
    setMaxCookTime("");
    setPage(1);
    // Trigger fetch after clearing
    setTimeout(() => fetchRecipes(), 0);
  };

  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const openRecipeModal = (recipe: StaticRecipe) => {
    // Transform StaticRecipe to match RecipeModal's expected format
    const transformedRecipe = {
      image: recipe.image_url || "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
      title: recipe.title,
      description: `${recipe.difficulty.charAt(0).toUpperCase() + recipe.difficulty.slice(1)} • ${recipe.prep_time + recipe.cook_time} mins • ${recipe.servings} servings`,
      ingredients: recipe.ingredients,
      instructions: recipe.instructions,
    };
    setSelectedRecipe(transformedRecipe);
    setIsModalOpen(true);
  };

  const closeRecipeModal = () => {
    setIsModalOpen(false);
    setSelectedRecipe(null);
  };

  const totalPages = Math.ceil(totalRecipes / pageSize);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy":
        return "bg-green-100 text-green-700 border-green-300";
      case "medium":
        return "bg-yellow-100 text-yellow-700 border-yellow-300";
      case "hard":
        return "bg-red-100 text-red-700 border-red-300";
      default:
        return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-red-50 pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-gradient-to-r from-orange-400 to-red-400 p-3 rounded-2xl">
              <ChefHat className="w-12 h-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent mb-4">
            Recipe Collection
          </h1>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Discover delicious recipes from around the world. Browse, filter, and find your next favorite dish!
          </p>
          <div className="mt-4 text-sm text-gray-500">
            {totalRecipes} recipes available
          </div>
        </div>

        {/* Search and Filter Section */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          {/* Search Bar */}
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by ingredients (e.g., paneer, tomato)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center justify-center gap-2 px-6 py-3 rounded-xl transition font-medium ${
                showFilters
                  ? "bg-orange-500 text-white"
                  : "bg-orange-100 text-orange-600 hover:bg-orange-200"
              }`}
            >
              <Filter className="w-5 h-5" />
              Filters
            </button>
            <button
              onClick={handleSearch}
              className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-xl hover:from-orange-600 hover:to-red-700 transition font-medium shadow-md"
            >
              Search
            </button>
          </div>

          {/* Active Filters Display */}
          {(searchQuery || selectedDifficulty || selectedTags.length > 0 || maxPrepTime || maxCookTime) && (
            <div className="flex flex-wrap gap-2 items-center mb-4 pb-4 border-b border-gray-200">
              <span className="text-sm font-medium text-gray-600">Active Filters:</span>
              {searchQuery && (
                <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                  Ingredients: {searchQuery}
                </span>
              )}
              {selectedDifficulty && (
                <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                  {selectedDifficulty}
                </span>
              )}
              {selectedTags.map((tag) => (
                <span key={tag} className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                  {tag}
                </span>
              ))}
              {maxPrepTime && (
                <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                  Prep ≤ {maxPrepTime}m
                </span>
              )}
              {maxCookTime && (
                <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm">
                  Cook ≤ {maxCookTime}m
                </span>
              )}
              <button
                onClick={handleClearFilters}
                className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm hover:bg-red-200 transition flex items-center gap-1"
              >
                <X className="w-3 h-3" />
                Clear All
              </button>
            </div>
          )}

          {/* Expanded Filters */}
          {showFilters && (
            <div className="space-y-6 pt-4 border-t border-gray-200">
              {/* Difficulty Filter */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Difficulty Level
                </label>
                <div className="flex flex-wrap gap-2">
                  {difficulties.map((diff) => (
                    <button
                      key={diff}
                      onClick={() =>
                        setSelectedDifficulty(selectedDifficulty === diff ? "" : diff)
                      }
                      className={`px-4 py-2 rounded-xl border-2 transition font-medium capitalize ${
                        selectedDifficulty === diff
                          ? "bg-orange-500 text-white border-orange-500"
                          : "bg-white text-gray-700 border-gray-300 hover:border-orange-300"
                      }`}
                    >
                      {diff}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags Filter */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Tags & Categories
                </label>
                <div className="flex flex-wrap gap-2">
                  {availableTags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => toggleTag(tag)}
                      className={`px-4 py-2 rounded-xl border-2 transition font-medium capitalize ${
                        selectedTags.includes(tag)
                          ? "bg-orange-500 text-white border-orange-500"
                          : "bg-white text-gray-700 border-gray-300 hover:border-orange-300"
                      }`}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>

              {/* Time Filters */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Max Prep Time (minutes)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 30"
                    value={maxPrepTime}
                    onChange={(e) => setMaxPrepTime(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Max Cook Time (minutes)
                  </label>
                  <input
                    type="number"
                    placeholder="e.g., 60"
                    value={maxCookTime}
                    onChange={(e) => setMaxCookTime(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl mb-8">
            <p className="font-medium">Error: {error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-12 h-12 text-orange-500 animate-spin mb-4" />
            <p className="text-gray-600 text-lg">Loading delicious recipes...</p>
          </div>
        )}

        {/* No Results */}
        {!loading && !error && recipes.length === 0 && (
          <div className="text-center py-20">
            <div className="bg-gradient-to-r from-orange-400 to-red-400 p-4 rounded-2xl inline-block mb-4">
              <Search className="w-12 h-12 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-gray-800 mb-2">No recipes found</h3>
            <p className="text-gray-600 mb-6">
              Try adjusting your filters or search terms
            </p>
            {(searchQuery || selectedDifficulty || selectedTags.length > 0 || maxPrepTime || maxCookTime) && (
              <button
                onClick={handleClearFilters}
                className="px-6 py-3 bg-orange-500 text-white rounded-xl hover:bg-orange-600 transition font-medium"
              >
                Clear Filters
              </button>
            )}
          </div>
        )}

        {/* Recipe Grid */}
        {!loading && !error && recipes.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {recipes.map((recipe) => (
                <div
                  key={recipe._id}
                  onClick={() => openRecipeModal(recipe)}
                  className="bg-white rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden cursor-pointer transform hover:-translate-y-1 border border-gray-100"
                >
                  {/* Recipe Image */}
                  <div className="relative h-48 overflow-hidden bg-gradient-to-br from-orange-100 to-red-100">
                    {recipe.image_url ? (
                      <img
                        src={recipe.image_url}
                        alt={recipe.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800";
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <ChefHat className="w-16 h-16 text-orange-300" />
                      </div>
                    )}
                    <div className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-semibold border-2 backdrop-blur-sm ${getDifficultyColor(recipe.difficulty)}`}>
                      {recipe.difficulty}
                    </div>
                  </div>

                  {/* Recipe Info */}
                  <div className="p-5">
                    <h3 className="text-lg font-bold text-gray-800 mb-2 line-clamp-2">
                      {recipe.title}
                    </h3>

                    {/* Tags */}
                    {recipe.tags && recipe.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {recipe.tags.slice(0, 3).map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-orange-50 text-orange-600 text-xs rounded-lg font-medium"
                          >
                            {tag}
                          </span>
                        ))}
                        {recipe.tags.length > 3 && (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-lg font-medium">
                            +{recipe.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Meta Info */}
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-orange-500" />
                        <span>{recipe.prep_time + recipe.cook_time} mins</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4 text-orange-500" />
                        <span>{recipe.servings} servings</span>
                      </div>
                    </div>

                    {/* Nutrition Info */}
                    {recipe.nutrition && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="grid grid-cols-4 gap-2 text-xs">
                          <div className="text-center">
                            <p className="font-semibold text-gray-800">{recipe.nutrition.calories}</p>
                            <p className="text-gray-500">cal</p>
                          </div>
                          <div className="text-center">
                            <p className="font-semibold text-gray-800">{recipe.nutrition.protein}g</p>
                            <p className="text-gray-500">protein</p>
                          </div>
                          <div className="text-center">
                            <p className="font-semibold text-gray-800">{recipe.nutrition.carbs}g</p>
                            <p className="text-gray-500">carbs</p>
                          </div>
                          <div className="text-center">
                            <p className="font-semibold text-gray-800">{recipe.nutrition.fat}g</p>
                            <p className="text-gray-500">fat</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-orange-50 hover:border-orange-300 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
                >
                  Previous
                </button>
                
                <div className="flex gap-2">
                  {[...Array(Math.min(5, totalPages))].map((_, idx) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = idx + 1;
                    } else if (page <= 3) {
                      pageNum = idx + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + idx;
                    } else {
                      pageNum = page - 2 + idx;
                    }

                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`px-4 py-2 rounded-lg font-medium transition ${
                          page === pageNum
                            ? "bg-gradient-to-r from-orange-500 to-red-600 text-white shadow-md"
                            : "bg-white border border-gray-300 hover:bg-orange-50 hover:border-orange-300"
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-orange-50 hover:border-orange-300 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
                >
                  Next
                </button>
              </div>
            )}

            {/* Page Info */}
            <div className="text-center mt-4 text-sm text-gray-600">
              Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, totalRecipes)} of {totalRecipes} recipes
            </div>
          </>
        )}
      </div>

      {/* Recipe Modal */}
      <RecipeModal
        isOpen={isModalOpen}
        onClose={closeRecipeModal}
        recipe={selectedRecipe}
      />
    </div>
  );
};

export default StaticRecipes;