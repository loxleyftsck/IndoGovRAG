/**
 * Auth utilities and session helpers for IndoGovRAG frontend
 */

import { auth } from "@/app/api/auth/[...nextauth]/route";

/**
 * Get the current server-side session.
 * Use in Server Components and Server Actions.
 */
export async function getSession() {
  return await auth();
}

/**
 * Get the current user ID from session.
 * Returns null if not authenticated.
 */
export async function getUserId(): Promise<string | null> {
  const session = await getSession();
  return (session?.user?.id as string) || null;
}

/**
 * Check if user is authenticated.
 */
export async function isAuthenticated(): Promise<boolean> {
  const session = await getSession();
  return !!session?.user;
}

/**
 * Type definition for session user.
 */
export interface SessionUser {
  id: string;
  email: string;
  name: string;
  image?: string;
  provider?: string;
}
