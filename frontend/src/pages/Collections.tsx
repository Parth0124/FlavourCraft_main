import { useState, useEffect } from "react";
import { ChefHat, Clock, Filter, RotateCcw, Calendar, Utensils, Leaf, Globe, ArrowLeft, ChevronRight } from "lucide-react";
import { recipeService } from "../lib/api/services/recepie.service";

// Import cuisine images
import italianImg from "/src/assets/italian.webp";
import chineseImg from "/src/assets/chinese.jpg";
import mexicanImg from "/src/assets/mexican.jpg";
import indianImg from "/src/assets/indian.jpg";
import japaneseImg from "/src/assets/japanese.jpeg";
import thaiImg from "/src/assets/thai.jpg";
import frenchImg from "/src/assets/french.jpg";
import americanImg from "/src/assets/american.png";
import greekImg from "/src/assets/greek.jpeg";
import koreanImg from "/src/assets/korean.jpg";
import vietnameseImg from "/src/assets/vietnamese.webp";
import caribbeanImg from "/src/assets/caribbean.jpeg";
import ethiopianImg from "/src/assets/ethiopian.jpg";
import germanImg from "/src/assets/german.png";
import indonesianImg from "/src/assets/indonesian.jpg";
import lebaneseImg from "/src/assets/lebanese.jpg";
import moroccanImg from "/src/assets/moroccon.jpeg";
import spanishImg from "/src/assets/Spanish.jpg";
import britishImg from "/src/assets/british.jpg";


type CombinedRecipe = {
  id: string;
  title: string;
  image: string;
  cuisine: string;
  cuisineType?: string;
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
  dietaryPreferences?: string[];
};

type ViewMode = 'cuisines' | 'dishes' | 'recipe';

const CollectionsPage = () => {
  const [recipes, setRecipes] = useState<CombinedRecipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCuisineType, setSelectedCuisineType] = useState<string>("");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("All");
  const [selectedRecipe, setSelectedRecipe] = useState<CombinedRecipe | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('cuisines');

  useEffect(() => {
    fetchAllRecipes();
  }, []);

  const fetchAllRecipes = async () => {
    try {
      const generatedData = await recipeService.getAllGeneratedRecipes(1, 100);
      console.log("📥 Raw API Response:", generatedData);
      
      if (generatedData.recipes && generatedData.recipes.length > 0) {
        console.log("🔍 First RAW recipe from API:", generatedData.recipes[0]);
        console.log("🔍 Available fields:", Object.keys(generatedData.recipes[0]));
      }
      
      const generatedRecipes: CombinedRecipe[] = (generatedData.recipes || []).map((recipe: any) => {
        console.log("🔍 Checking recipe fields:");
        console.log("  - cuisine_type:", recipe.cuisine_type);
        console.log("  - cuisineType:", recipe.cuisineType);
        console.log("  - dietary_preferences:", recipe.dietary_preferences);
        console.log("  - dietaryPreferences:", recipe.dietaryPreferences);
        console.log("  - options:", recipe.options);
        
        const cuisineType = recipe.cuisine_type || 
                           recipe.cuisineType || 
                           recipe.options?.cuisine_type ||
                           "Other";
                           
        const dietaryPreferences = recipe.dietary_preferences || 
                                  recipe.dietaryPreferences || 
                                  recipe.options?.dietary_preferences ||
                                  undefined;
        
        console.log("✅ Mapped values:");
        console.log("  - cuisineType:", cuisineType);
        console.log("  - dietaryPreferences:", dietaryPreferences);
        
        return {
          id: recipe.id,
          title: recipe.recipe.title,
          image: recipe.image_urls?.medium_url,
          cuisine: "Community",
          cuisineType: cuisineType,
          difficulty: recipe.recipe.difficulty,
          prepTime: recipe.recipe.estimated_time,
          description: recipe.recipe.tips || recipe.recipe.steps[0] || "Delicious community recipe",
          ingredients: recipe.ingredients_used,
          instructions: recipe.recipe.steps.map((step: string, idx: number) => `${idx + 1}. ${step}`).join("\n"),
          servings: recipe.recipe.servings,
          isStatic: false,
          createdAt: recipe.created_at,
          tips: recipe.recipe.tips,
          dietaryPreferences: dietaryPreferences,
        };
      });
      
      console.log("📦 Transformed Recipes:", generatedRecipes);
      console.log("📦 First recipe sample:", generatedRecipes[0]);
      setRecipes(generatedRecipes);
    } catch (error) {
      console.error("❌ Error fetching recipes:", error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique cuisine types from recipes
  const cuisineTypes = Array.from(new Set(recipes.map(r => r.cuisineType).filter(Boolean))) as string[];
  
  // Debug: Log all unique cuisine types
  useEffect(() => {
    if (cuisineTypes.length > 0) {
      console.log("🌍 All unique cuisine types:", cuisineTypes);
      console.log("🌍 Number of cuisines:", cuisineTypes.length);
    }
  }, [cuisineTypes]);
  
  // Get recipes for selected cuisine type with difficulty filter
  const getRecipesForCuisine = (cuisineType: string) => {
    return recipes.filter(r => 
      r.cuisineType === cuisineType && 
      (selectedDifficulty === "All" || r.difficulty.toLowerCase() === selectedDifficulty.toLowerCase())
    );
  };

  const currentCuisineRecipes = selectedCuisineType ? getRecipesForCuisine(selectedCuisineType) : [];

  const resetFilters = () => {
    setSelectedDifficulty("All");
  };

  const handleCuisineClick = (cuisineType: string) => {
    setSelectedCuisineType(cuisineType);
    setViewMode('dishes');
    resetFilters();
  };

  const handleDishClick = (recipe: CombinedRecipe) => {
    console.log("🔍 Opening recipe details:", recipe);
    setSelectedRecipe(recipe);
    setViewMode('recipe');
  };

  const handleBackToCuisines = () => {
    setViewMode('cuisines');
    setSelectedCuisineType("");
    resetFilters();
  };

  const handleBackToDishes = () => {
    setViewMode('dishes');
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

  // Cuisine images mapping using imported images
  const getCuisineImage = (cuisine: string) => {
    console.log("🖼️ Getting image for cuisine:", cuisine);
    
    const images: Record<string, string> = {
      'Italian': italianImg,
      'italian': italianImg,
      'Chinese': chineseImg,
      'chinese': chineseImg,
      'Mexican': mexicanImg,
      'mexican': mexicanImg,
      'Indian': indianImg,
      'indian': indianImg,
      'Japanese': japaneseImg,
      'japanese': japaneseImg,
      'Thai': thaiImg,
      'thai': thaiImg,
      'French': frenchImg,
      'french': frenchImg,
      'American': americanImg,
      'american': americanImg,
      'Mediterranean': greekImg,
      'mediterranean': greekImg,
      'Korean': koreanImg,
      'korean': koreanImg,
      'Vietnamese': vietnameseImg,
      'vietnamese': vietnameseImg,
      'Greek': greekImg,
      'greek': greekImg,
      'Caribbean': caribbeanImg,
      'caribbean': caribbeanImg,
      'Ethiopian': ethiopianImg,
      'ethiopian': ethiopianImg,
      'German': germanImg,
      'german': germanImg,
      'Indonesian': indonesianImg,
      'indonesian': indonesianImg,
      'Lebanese': lebaneseImg,
      'lebanese': lebaneseImg,
      'Moroccan': moroccanImg,
      'moroccan': moroccanImg,
      'Spanish': spanishImg,
      'spanish': spanishImg,
      'British': britishImg,
      'british': britishImg,
    };
    
    const selectedImage = images[cuisine] || images[cuisine.toLowerCase()] || italianImg;
    console.log("✅ Selected image for", cuisine, ":", selectedImage);
    
    return selectedImage;
  };

  // Cuisine icons mapping (for header display)
  const getCuisineIcon = (cuisine: string) => {
    const icons: Record<string, string> = {
      'Italian': '🍝',
      'Chinese': '🥢',
      'Mexican': '🌮',
      'Indian': '🍛',
      'Japanese': '🍱',
      'Thai': '🍜',
      'French': '🥐',
      'American': '🍔',
      'Mediterranean': '🫒',
      'Korean': '🍲',
      'Vietnamese': '🥗',
      'Greek': '🥙',
      'Caribbean': '🏝️',
      'Ethiopian': '🌾',
      'German': '🍺',
      'Indonesian': '🌴',
      'Lebanese': '🥙',
      'Moroccan': '🏺',
      'Spanish': '🥘',
      'British': '☕',
    };
    return icons[cuisine] || '🍽️';
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
        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-orange-500 border-t-transparent"></div>
            <p className="mt-4 text-gray-600">Loading recipes...</p>
          </div>
        )}

        {/* VIEW 1: Cuisines Grid */}
        {!loading && viewMode === 'cuisines' && (
          <>
            {/* Header */}
            <div className="text-center mb-12 space-y-4">
              <h1 className="text-5xl font-bold">
                <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
                  Explore Cuisines
                </span>
              </h1>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Discover recipes from around the world, created by our community
              </p>

              {/* Stats Bar */}
              <div className="flex items-center justify-center space-x-8 pt-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{recipes.length}</div>
                  <div className="text-sm text-gray-500">Total Recipes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{cuisineTypes.length}</div>
                  <div className="text-sm text-gray-500">Cuisines</div>
                </div>
              </div>
            </div>

            {/* Cuisine Cards Grid */}
            {cuisineTypes.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {cuisineTypes.map((cuisineType) => {
                  const cuisineRecipeCount = recipes.filter(r => r.cuisineType === cuisineType).length;
                  return (
                    <div
                      key={cuisineType}
                      onClick={() => handleCuisineClick(cuisineType)}
                      className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transform hover:-translate-y-2 transition-all duration-300 cursor-pointer group"
                    >
                      <div className="relative h-40 bg-gradient-to-br from-orange-200 to-red-200 overflow-hidden">
                        <img 
                          src={getCuisineImage(cuisineType)} 
                          alt={cuisineType}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                        />
                        <div className="absolute inset-0 bg-black opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
                        
                        {/* Cuisine Name Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent flex items-end justify-center pb-4">
                          <h3 className="text-2xl font-bold text-white">{cuisineType}</h3>
                        </div>
                      </div>
                      
                      <div className="p-5 space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">
                            {cuisineRecipeCount} {cuisineRecipeCount === 1 ? 'recipe' : 'recipes'}
                          </span>
                          <span className="text-orange-600 font-semibold flex items-center gap-1">
                            View All 
                            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-20">
                <ChefHat className="w-20 h-20 text-gray-300 mx-auto mb-4" />
                <h3 className="text-2xl font-semibold text-gray-700 mb-2">No cuisines available</h3>
                <p className="text-gray-500">Check back later for new recipes!</p>
              </div>
            )}
          </>
        )}

        {/* VIEW 2: Dishes List for Selected Cuisine */}
        {!loading && viewMode === 'dishes' && (
          <>
            {/* Header with Back Button */}
            <div className="mb-8">
              <button
                onClick={handleBackToCuisines}
                className="flex items-center gap-2 text-orange-600 hover:text-orange-700 font-semibold mb-6 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Cuisines
              </button>

              <div className="text-center space-y-4">
                <h1 className="text-5xl font-bold flex items-center justify-center gap-3">
                  <span className="text-5xl">{getCuisineIcon(selectedCuisineType)}</span>
                  <span className="bg-gradient-to-r from-orange-600 to-red-500 bg-clip-text text-transparent">
                    {selectedCuisineType}
                  </span>
                </h1>
                <p className="text-xl text-gray-600">
                  {currentCuisineRecipes.length} delicious {currentCuisineRecipes.length === 1 ? 'recipe' : 'recipes'} to explore
                </p>
              </div>
            </div>

            {/* Difficulty Filter */}
            <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-orange-500" />
                  <label className="font-medium text-gray-700">Difficulty:</label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="border border-gray-300 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500 bg-white"
                  >
                    <option value="All">All</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>

                {selectedDifficulty !== "All" && (
                  <button
                    onClick={resetFilters}
                    className="flex items-center gap-2 bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-2 rounded-xl font-medium hover:from-orange-600 hover:to-red-600 transition-all duration-200 shadow-md ml-auto"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset Filter
                  </button>
                )}
              </div>
            </div>

            {/* Dishes Grid */}
            {currentCuisineRecipes.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {currentCuisineRecipes.map((recipe) => (
                  <div
                    key={recipe.id}
                    onClick={() => handleDishClick(recipe)}
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
            ) : (
              <div className="text-center py-20">
                <ChefHat className="w-20 h-20 text-gray-300 mx-auto mb-4" />
                <h3 className="text-2xl font-semibold text-gray-700 mb-2">No recipes found</h3>
                <p className="text-gray-500 mb-6">Try adjusting your difficulty filter</p>
                <button
                  onClick={resetFilters}
                  className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-orange-600 hover:to-red-600"
                >
                  Reset Filter
                </button>
              </div>
            )}
          </>
        )}

        {/* VIEW 3: Detailed Recipe */}
        {!loading && viewMode === 'recipe' && selectedRecipe && (
          <div className="max-w-4xl mx-auto">
            {/* Back Button */}
            <button
              onClick={handleBackToDishes}
              className="flex items-center gap-2 text-orange-600 hover:text-orange-700 font-semibold mb-6 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to {selectedCuisineType} Recipes
            </button>

            {/* Recipe Detail Card */}
            <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
              {/* Recipe Header with Image */}
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
                    {selectedRecipe.cuisineType && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-600 flex items-center gap-1">
                        <Globe className="w-3 h-3" />
                        {selectedRecipe.cuisineType}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Recipe Content */}
              <div className="p-6 md:p-8 space-y-6">
                {/* Dietary Preferences Section */}
                {selectedRecipe.dietaryPreferences && selectedRecipe.dietaryPreferences.length > 0 && (
                  <div className="bg-green-50 rounded-xl p-4 border border-green-100">
                    <div className="flex items-center gap-2 mb-3">
                      <Leaf className="w-5 h-5 text-green-600" />
                      <h3 className="text-lg font-bold text-gray-800">Dietary Information</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {selectedRecipe.dietaryPreferences.map((pref, index) => (
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

                {/* Back Button */}
                <div className="flex justify-center pt-4">
                  <button
                    onClick={handleBackToDishes}
                    className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-3 rounded-xl font-semibold hover:from-orange-600 hover:to-red-600 transition-all duration-200 shadow-lg"
                  >
                    Back to Recipes
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CollectionsPage;