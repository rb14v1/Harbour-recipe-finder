export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface Recipe {
  id: number;
  title: string;
  ingredients: string;
  instructions: string;
  created_at: string;
  updated_at: string;
}

export interface SearchMatch {
  recipe_id: number;
  title: string;
  score: number;
}

export interface SearchResponse {
  matches: SearchMatch[];
  suggestion: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}
