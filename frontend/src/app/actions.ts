"use server";

import { currentUser } from "@clerk/nextjs/server";

// We strictly use Clerk for identity. 
// Data operations (Chat, Repos) are handled by the Python Backend API.

export async function getCurrentUser() {
  const user = await currentUser();
  if (!user) return null;

  return {
    id: user.id, // Clerk ID (matches 'external_id' in Python DB)
    email: user.emailAddresses[0]?.emailAddress,
    fullName: user.firstName ? `${user.firstName} ${user.lastName}` : user.username
  };
}

