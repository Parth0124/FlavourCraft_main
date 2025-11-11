import { useState, useEffect } from "react";
import { ChefHat, Clock, Filter, RotateCcw, X, Calendar, Utensils } from "lucide-react";
import { recipeService } from "../lib/api/services/recepie.service";
import type { GeneratedRecipeResponse } from "../types/api.types";

type CombinedRecipe = {
  id: string;
  title: string;
  image: string;
  cuisine: string;
  difficulty: string;
  prepTime: number;
  description: string;
  ingredients: string[];
  instructions: string;
  servings?: number;
  isStatic: boolean;
  username?: string;
  createdAt?: string;
  tips?: string;
};

const CollectionsPage = () => {
  const [recipes, setRecipes] = useState<CombinedRecipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCuisine, setSelectedCuisine] = useState<string>("All");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("All");
  const [selectedRecipe, setSelectedRecipe] = useState<CombinedRecipe | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchAllRecipes();
  }, []);

  const fetchAllRecipes = async () => {
    try {
      // Fetch ALL generated recipes (public access)
      const generatedData = await recipeService.getAllGeneratedRecipes(1, 100);
      console.log("Raw API Response:", generatedData);
      console.log("Number of recipes received:", generatedData.recipes?.length || 0);
      const generatedRecipes: CombinedRecipe[] = (generatedData.recipes || []).map((recipe: GeneratedRecipeResponse) => ({
        id: recipe.id,
        title: recipe.recipe.title,
        image: recipe.image_urls?.medium_url || "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
        cuisine: "Community",
        difficulty: recipe.recipe.difficulty,
        prepTime: recipe.recipe.estimated_time,
        description: recipe.recipe.tips || recipe.recipe.steps[0] || "Delicious community recipe",
        ingredients: recipe.ingredients_used,
        instructions: recipe.recipe.steps.map((step, idx) => `${idx + 1}. ${step}`).join("\n"),
        servings: recipe.recipe.servings,
        isStatic: false,
        createdAt: recipe.created_at,
        tips: recipe.recipe.tips,
      }));
      console.log("Transformed Recipes:", generatedRecipes);
      console.log("First recipe sample:", generatedRecipes[0]);
      setRecipes(generatedRecipes);
    } catch (error) {
      console.error("Error fetching recipes:", error);
    } finally {
      setLoading(false);
    }
  };

  const cuisines = ["All", ...Array.from(new Set(recipes.map(r => r.cuisine)))];
  const difficulties = ["All", "easy", "Easy", "medium", "Medium", "hard", "Hard"];

  const filteredRecipes = recipes.filter(
    (r) =>
      (selectedCuisine === "All" || r.cuisine === selectedCuisine) &&
      (selectedDifficulty === "All" || r.difficulty.toLowerCase() === selectedDifficulty.toLowerCase())
  );

  const groupedByCuisine = filteredRecipes.reduce((acc, recipe) => {
    if (!acc[recipe.cuisine]) {
      acc[recipe.cuisine] = [];
    }
    acc[recipe.cuisine].push(recipe);
    return acc;
  }, {} as Record<string, CombinedRecipe[]>);

  const resetFilters = () => {
    setSelectedCuisine("All");
    setSelectedDifficulty("All");
  };

  const openModal = (recipe: CombinedRecipe) => {
    setSelectedRecipe(recipe);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedRecipe(null);
  };

  const getDifficultyColor = (difficulty: string) => {
    const lower = difficulty.toLowerCase();
    switch (lower) {
      case "easy": return "text-green-600 bg-green-50";
      case "medium": return "text-orange-600 bg-orange-50";
      case "hard": return "text-red-600 bg-red-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <>
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
                Community Recipe Collections
              </span>
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Explore delicious recipes created by our amazing community of home chefs
            </p>

            {/* Stats Bar */}
            {!loading && recipes.length > 0 && (
              <div className="flex items-center justify-center space-x-8 pt-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{recipes.length}</div>
                  <div className="text-sm text-gray-500">Total Recipes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {recipes.filter(r => r.difficulty.toLowerCase() === 'easy').length}
                  </div>
                  <div className="text-sm text-gray-500">Easy Recipes</div>
                </div>
              </div>
            )}
          </div>

          {/* Filters */}
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Filter className="w-5 h-5 text-orange-500" />
                <label className="font-medium text-gray-700">Cuisine:</label>
                <select
                  value={selectedCuisine}
                  onChange={(e) => setSelectedCuisine(e.target.value)}
                  className="border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500 bg-white"
                >
                  {cuisines.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <label className="font-medium text-gray-700">Difficulty:</label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
                  className="border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500 bg-white"
                >
                  {Array.from(new Set(difficulties.map(d => d.toLowerCase()))).map((d) => (
                    <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={resetFilters}
                className="flex items-center gap-2 bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-2 rounded-xl font-medium hover:from-orange-600 hover:to-red-600 transition-all duration-200 shadow-md ml-auto"
              >
                <RotateCcw className="w-4 h-4" />
                Reset Filters
              </button>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center py-20">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-orange-500 border-t-transparent"></div>
              <p className="mt-4 text-gray-600">Loading recipes...</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && filteredRecipes.length === 0 && (
            <div className="text-center py-20">
              <ChefHat className="w-20 h-20 text-gray-300 mx-auto mb-4" />
              <h3 className="text-2xl font-semibold text-gray-700 mb-2">No recipes found</h3>
              <p className="text-gray-500 mb-6">Try adjusting your filters</p>
              <button
                onClick={resetFilters}
                className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-orange-600 hover:to-red-600"
              >
                Reset Filters
              </button>
            </div>
          )}

          {/* Recipes Grouped by Cuisine */}
          {!loading && Object.keys(groupedByCuisine).length > 0 && (
            <div className="space-y-12">
              {Object.entries(groupedByCuisine).map(([cuisine, cuisineRecipes]) => (
                <div key={cuisine}>
                  {/* Cuisine Header */}
                  <div className="mb-6">
                    <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                      <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
                        {cuisine}
                      </span>
                      <span className="text-lg text-gray-500 font-normal">
                        ({cuisineRecipes.length} recipes)
                      </span>
                    </h2>
                    <div className="h-1 w-20 bg-gradient-to-r from-orange-500 to-red-500 rounded-full mt-2"></div>
                  </div>

                  {/* Recipe Cards */}
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {cuisineRecipes.map((recipe) => (
                      <div
                        key={recipe.id}
                        onClick={() => openModal(recipe)}
                        className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transform hover:-translate-y-2 transition-all duration-300 cursor-pointer"
                      >
                        {/* Recipe Image */}
                        <div className="relative h-48 bg-gradient-to-br from-orange-200 to-red-200">
                          {recipe.image ? (
                            <img
                              src={recipe.image}
                              alt={recipe.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <ChefHat className="w-16 h-16 text-orange-400" />
                            </div>
                          )}
                          
                          {/* Difficulty Badge */}
                          <div className="absolute top-3 left-3">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getDifficultyColor(recipe.difficulty)}`}>
                              {recipe.difficulty}
                            </span>
                          </div>
                        </div>

                        {/* Recipe Content */}
                        <div className="p-5 space-y-3">
                          <h3 className="text-xl font-bold text-gray-800 line-clamp-2">
                            {recipe.title}
                          </h3>

                          <p className="text-gray-600 text-sm line-clamp-2">
                            {recipe.description}
                          </p>

                          {/* Recipe Info */}
                          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                            <div className="flex items-center space-x-1 text-gray-600">
                              <Clock className="w-4 h-4" />
                              <span className="text-sm">{recipe.prepTime} mins</span>
                            </div>
                            <div className="flex items-center space-x-1 text-gray-600">
                              <Utensils className="w-4 h-4" />
                              <span className="text-sm">{recipe.servings || 4} servings</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Recipe Modal */}
      {isModalOpen && selectedRecipe && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            {/* Modal Header with Image */}
            <div className="relative h-64 md:h-80 bg-gradient-to-br from-orange-200 to-red-200">
              {selectedRecipe.image ? (
                <img
                  src={selectedRecipe.image}
                  alt={selectedRecipe.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <ChefHat className="w-20 h-20 text-orange-400" />
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
              
              {/* Close Button */}
              <button
                onClick={closeModal}
                className="absolute top-4 right-4 bg-white rounded-full p-2 hover:bg-gray-100 transition-colors"
              >
                <X className="w-6 h-6 text-gray-800" />
              </button>

              {/* Title Overlay */}
              <div className="absolute bottom-0 left-0 right-0 p-6">
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">
                  {selectedRecipe.title}
                </h2>
                <div className="flex flex-wrap items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getDifficultyColor(selectedRecipe.difficulty)}`}>
                    {selectedRecipe.difficulty}
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-600">
                    Community Recipe
                  </span>
                </div>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 md:p-8 space-y-6">
              {/* Recipe Meta Info */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pb-6 border-b border-gray-200">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-orange-500" />
                  <div>
                    <div className="text-xs text-gray-500">Prep Time</div>
                    <div className="font-semibold text-gray-800">{selectedRecipe.prepTime} mins</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Utensils className="w-5 h-5 text-orange-500" />
                  <div>
                    <div className="text-xs text-gray-500">Servings</div>
                    <div className="font-semibold text-gray-800">{selectedRecipe.servings || 4}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-orange-500" />
                  <div>
                    <div className="text-xs text-gray-500">Created</div>
                    <div className="font-semibold text-gray-800">{formatDate(selectedRecipe.createdAt)}</div>
                  </div>
                </div>
              </div>

              {/* Ingredients Section */}
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
                    Ingredients
                  </span>
                </h3>
                <ul className="space-y-2">
                  {selectedRecipe.ingredients.map((ingredient, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <span className="text-orange-500 mt-1">•</span>
                      <span className="text-gray-700">{ingredient}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Instructions Section */}
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                  <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
                    Instructions
                  </span>
                </h3>
                <div className="space-y-3 whitespace-pre-line text-gray-700 leading-relaxed">
                  {selectedRecipe.instructions}
                </div>
              </div>

              {/* Tips Section */}
              {selectedRecipe.tips && (
                <div className="bg-orange-50 rounded-xl p-5">
                  <h3 className="text-xl font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <span className="text-orange-600">💡 Chef's Tips</span>
                  </h3>
                  <p className="text-gray-700">{selectedRecipe.tips}</p>
                </div>
              )}

              {/* Close Button */}
              <div className="flex justify-center pt-4">
                <button
                  onClick={closeModal}
                  className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-3 rounded-xl font-semibold hover:from-orange-600 hover:to-red-600 transition-all duration-200 shadow-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default CollectionsPage;