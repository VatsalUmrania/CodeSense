import { auth } from "@clerk/nextjs/server";

// Helper to get the token on the server side (for API calls to Python backend)
export async function getToken() {
  const { getToken } = await auth();
  return await getToken();
}

// Helper to get the current session claims
export async function getSession() {
  const { userId, sessionClaims } = await auth();
  return {
    userId,
    claims: sessionClaims
  };
}