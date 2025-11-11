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

export interface RecipeGenerationRequest {
  ingredients: string[];
  dietary_preferences?: string[];
  cuisine_type?: string;
  cooking_time?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
}

export interface ImageUrls {
  url: string;           // Full size
  thumbnail_url: string; // 150x150
  medium_url: string;    // 500x500
  public_id: string;
}

export interface GeneratedRecipeResponse {
  id: string;
  recipe: GeneratedRecipe;
  ingredients_used: string[];
  created_at: string;
  is_favorite: boolean;
  image_urls?: ImageUrls;
  username?: string;  // Username of the creator
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