const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendMessage(message: string, history: any[]) {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      message, 
      history 
    }),
  });

  if (!response.ok) throw new Error("Failed to fetch response");
  
  // We will handle streaming later, for now just JSON
  return response.json();
}