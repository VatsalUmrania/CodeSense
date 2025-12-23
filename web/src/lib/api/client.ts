import type { paths } from './types'; 
import createClient from 'openapi-fetch';

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(status: number, data: any) {
    super(`API Error ${status}: ${data?.message || JSON.stringify(data)}`);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

// 1. Clean URL Handling
const RAW_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_BASE_URL = RAW_URL.replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');

// 2. Initialize Client with Credentials
export const client = createClient<paths>({
  baseUrl: API_BASE_URL,
  
  // --- FIX: FORCE CREDENTIALS ---
  // This tells the browser: "Send cookies even though the backend is on a different port"
  fetch: async (url, init) => {
    return fetch(url, { 
      ...init, 
      credentials: "include", 
    });
  },
});

client.use({
  async onRequest({ request }) {
    // Server-Side: Manually pass cookies (RSC/Server Actions)
    if (typeof window === 'undefined') {
      try {
        const { cookies } = await import("next/headers");
        const cookieStore = await cookies();
        const sessionToken = cookieStore.get("session")?.value;
        
        if (sessionToken) {
          // Pass as Cookie Header (Backend likely reads this)
          request.headers.set('Cookie', `session=${sessionToken}`);
          // Optional: Pass as Bearer too if your backend supports both
          request.headers.set('Authorization', `Bearer ${sessionToken}`);
        }
      } catch (error) { 
        // Ignore errors in static generation context
      }
    }
    return request;
  },

  async onResponse({ response }) {
    if (!response.ok) {
      const err = await response.clone().json().catch(() => ({ 
        message: response.statusText 
      }));
      
      // Handle Auth Errors Gracefully (Optional)
      if (response.status === 401 || response.status === 403) {
         console.warn("User is not authenticated. Redirecting to login might be needed.");
      }

      throw new ApiError(response.status, err);
    }
    return undefined;
  },
});

export default client;