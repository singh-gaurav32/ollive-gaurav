import { apiJson } from "./client";
import type { User } from "../types";

export function listDemoUsers(): Promise<User[]> {
  return apiJson("/auth/users");
}

export function login(username: string): Promise<User> {
  return apiJson("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username }),
  });
}

export function logout(): Promise<void> {
  return apiJson("/auth/logout", { method: "POST" });
}

export function getCurrentUser(): Promise<User> {
  return apiJson("/auth/me", { skipAuthRedirect: true });
}
