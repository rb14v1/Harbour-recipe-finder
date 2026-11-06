import { apiClient } from "./client";
import type { Recipe, SearchResponse } from "../types";

export async function listRecipes(): Promise<Recipe[]> {
  const { data } = await apiClient.get("/recipes/");
  return data;
}

export async function getRecipe(id: number): Promise<Recipe> {
  const { data } = await apiClient.get(`/recipes/${id}/`);
  return data;
}

export async function createRecipe(payload: Pick<Recipe, "title" | "ingredients" | "instructions">): Promise<Recipe> {
  const { data } = await apiClient.post("/recipes/", payload);
  return data;
}

export async function updateRecipe(
  id: number,
  payload: Pick<Recipe, "title" | "ingredients" | "instructions">
): Promise<Recipe> {
  const { data } = await apiClient.put(`/recipes/${id}/`, payload);
  return data;
}

export async function deleteRecipe(id: number): Promise<void> {
  await apiClient.delete(`/recipes/${id}/`);
}

export async function searchRecipes(query: string, top_k?: number): Promise<SearchResponse> {
  const { data } = await apiClient.post("/search/", { query, top_k });
  return data;
}
