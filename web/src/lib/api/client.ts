import { getToken } from '@/lib/auth'; // Ensure this points to your Clerk auth helper
import type { paths } from './types'; // The generated schema
import createClient from 'openapi-fetch';

// 1. Initialize the Type-Safe Client
// openapi-fetch is a lightweight wrapper that pairs perfectly with openapi-typescript
// You might need to install it: npm install openapi-fetch
export const client = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
});

// 2. Add Auth Middleware
// This automatically injects the Bearer token into every request
client.use({
  async onRequest({ request }) {
    const token = await getToken(); // Fetches valid session token from Clerk
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`);
    }
    return request;
  },
  
  async onResponse({ response }) {
    // 3. Global Error Handling Strategy
    if (!response.ok) {
      // Clone the response because reading the body consumes it
      const err = await response.clone().json().catch(() => ({ 
        message: response.statusText 
      }));
      
      // Throwing here allows TanStack Query to catch it in 'isError'
      throw {
        status: response.status,
        data: err,
      };
    }
    return undefined; // If OK, proceed normally
  },
});

export default client;