import { apiClient } from "./client";
import type { AuthTokens, User } from "../types";

export async function register(
  email: string,
  password: string,
  first_name = "",
  last_name = ""
): Promise<AuthTokens & { user: User }> {
  const { data } = await apiClient.post("/auth/register/", {
    email,
    password,
    first_name,
    last_name,
  });
  return data;
}

export async function login(email: string, password: string): Promise<AuthTokens> {
  const { data } = await apiClient.post("/auth/login/", { email, password });
  return data;
}

export async function logout(refresh: string): Promise<void> {
  await apiClient.post("/auth/logout/", { refresh });
}

export async function fetchMe(): Promise<User> {
  const { data } = await apiClient.get("/auth/me/");
  return data;
}
