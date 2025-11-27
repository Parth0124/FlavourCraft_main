// User Types
export interface User {
  _id: string;
  username: string;
  email: string;
  created_at: string;
  last_login?: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  dietary_restrictions: string[];
  cuisine_preferences: string[];
  cooking_skill: 'beginner' | 'intermediate' | 'advanced';
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Recipe Types
export interface GeneratedRecipe {
  title: string;
  steps: string[];
  estimated_time: number;
  difficulty: 'easy' | 'medium' | 'hard';
  tips?: string;
  servings: number;
}

// ✅ FIXED: Added image_urls field
export interface RecipeGenerationRequest {
  ingredients: string[];
  dietary_preferences?: string[];
  cuisine_type?: string;
  cooking_time?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  image_urls?: ImageUrls;  // ✅ NEW - Include image URLs in request
}

export interface ImageUrls {
  url: string;           // Full size
  thumbnail_url: string; // 200x200
  medium_url: string;    // 600x600
  public_id: string;
}

export interface GeneratedRecipeResponse {
  id: string;
  recipe: GeneratedRecipe;
  ingredients_used: string[];
  created_at: string;
  is_favorite: boolean;
  image_urls?: ImageUrls;
  image_urls_list?: ImageUrls[];  // ✅ FIXED: Added for multi-image support
  cuisine_type?: string;  // ✅ FIXED: Added cuisine_type
  dietary_preferences?: string[];  // ✅ FIXED: Changed from string to string[]
  username?: string;  // Username of the creator
  options?: string[];  // ✅ FIXED: Added for recipe options/variations
}

// Recipe History Response
export interface RecipeHistoryResponse {
  recipes: GeneratedRecipeResponse[];
  total: number;
  page: number;
  page_size: number;
}

// Cuisine Types
export interface CuisineInfo {
  cuisine_type: string;
  recipe_count: number;
  description?: string;
  emoji?: string;
}

export interface CuisineCollection {
  cuisine_type: string;
  total_recipes: number;
  recipes: GeneratedRecipeResponse[];
  popular_ingredients: string[];
  avg_cooking_time?: number;
  difficulty_breakdown?: Record<string, number>;
  page_info?: {
    current_page: number;
    page_size: number;
    total_pages: number;
  };
}

export interface MultiUploadResult {
  status: string;
  total_images: number;
  ingredients: string[];
  image_urls_list: ImageUrls[];
  details: {
    total_detected: number;
    unique_ingredients: number;
  };
}

// Upload Types
export interface IngredientDetectionResult {
  status: string;
  filename: string;
  ingredients: string[];
  confidence: number;
  source: string;
  details: {
    local_detected: number;
    openai_detected: number;
    total_unique: number;
  };
  requires_verification: boolean;
  image_urls?: ImageUrls;  // ✅ FIXED: Added image_urls field
}

// Static Recipe Types
export interface StaticRecipe {
  _id: string;
  title: string;
  ingredients: string[];
  instructions: string;
  tags: string[];
  difficulty: 'easy' | 'medium' | 'hard';
  prep_time: number;
  cook_time: number;
  servings: number;
  nutrition?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
  image_url?: string;
}