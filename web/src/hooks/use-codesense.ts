import { useState } from "react";
import { toast } from "sonner";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/['"]+/g, '');

export interface Source {
  file: string;
  code: string;
  start_line?: number;
  end_line?: number;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export function useCodeSense() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [contextFiles, setContextFiles] = useState<Source[]>([]);

  // --- Action: Ingest Repo ---
  const ingestRepo = async (url: string) => {
    if (!url) {
        toast.error("Please enter a valid URL");
        return;
    }
    
    setIngestStatus("loading");
    const toastId = toast.loading("Cloning repository...");

    try {
      const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(url)}`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to initiate ingestion");
      
      const data = await res.json();
      
      // Handle Cache Hit
      if (data.status === "cached") {
        setIngestStatus("success");
        toast.success("Loaded from cache instantly!", { id: toastId });
        return;
      }

      // Handle New Ingestion (Polling)
      const taskId = data.task_id;
      const interval = setInterval(async () => {
        try {
            const statusRes = await fetch(`${API_URL}/status/${taskId}`);
            const statusData = await statusRes.json();
            
            if (statusData.status === "SUCCESS") {
              clearInterval(interval);
              setIngestStatus("success");
              toast.success("Repository indexed and ready!", { id: toastId });
            } else if (statusData.status === "FAILURE") {
              clearInterval(interval);
              setIngestStatus("error");
              toast.error(`Ingestion failed: ${statusData.result?.message}`, { id: toastId });
            }
        } catch (e) {
            clearInterval(interval);
            setIngestStatus("error");
            toast.error("Lost connection to server", { id: toastId });
        }
      }, 2000);

    } catch (error: any) {
      setIngestStatus("error");
      toast.error(error.message, { id: toastId });
    }
  };

  // --- Action: Send Message ---
  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMsg: Message = { role: "user", content };
    setMessages((prev) => [...prev, userMsg]);
    setIsChatting(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content }),
      });
      const data = await response.json();
      
      if (data.response && data.response.startsWith("AI Error")) {
         toast.error("AI Brain connection failed");
         setMessages((prev) => [...prev, { role: "assistant", content: "I'm having trouble connecting. Please try again." }]);
      } else {
         // Update Context Files in Sidebar
         if (data.context_used) {
            const newSources = data.context_used as Source[];
            setContextFiles(prev => {
                const existing = new Set(prev.map(p => p.file));
                const unique = newSources.filter(s => !existing.has(s.file));
                return [...prev, ...unique];
            });
         }
         
         setMessages((prev) => [...prev, { 
            role: "assistant", 
            content: data.response, 
            sources: data.context_used 
         }]);
      }
    } catch (error) {
      toast.error("Network error sending message");
      setMessages((prev) => [...prev, { role: "assistant", content: "Network error." }]);
    } finally {
      setIsChatting(false);
    }
  };

  const clearSession = () => {
      setMessages([]);
      setContextFiles([]);
      toast.info("Session cleared");
  };

  return {
    messages,
    isChatting,
    ingestStatus,
    contextFiles,
    ingestRepo,
    sendMessage,
    clearSession
  };
}