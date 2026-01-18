import { useState, useEffect } from "react";
import { toast } from "sonner";
import { useAuth } from "@clerk/nextjs";
import type { components } from "@/lib/api/types";

// --- Type Definitions (Matched to your Python Schemas) ---
export type Source = components["schemas"]["ChunkCitation"];

export interface Message {
  id?: string;
  role: "user" | "assistant";
  content: string;
  citations?: Source[];
}

export interface ChatSession {
  id: string;
  title: string;
  updated_at: string; // Python sends snake_case
}

// Ensure this points to /api/v1
const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export function useCodeSense() {
  const { getToken } = useAuth();

  const [messages, setMessages] = useState<Message[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const [repoId, setRepoId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [fileStructure, setFileStructure] = useState<string[]>([]);
  const [pinnedFiles, setPinnedFiles] = useState<string[]>([]);

  // --- Helper: Fetch with Bearer Token ---
  const fetchAPI = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getToken();
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (token) headers.set("Authorization", `Bearer ${token}`);

    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API Request Failed");
    }
    return res.json();
  };

  // --- Session Management ---
  const loadSessions = async () => {
    if (!repoId) return; // In V2, sessions might not be strictly filtered by repo in the list endpoint, check your API
    try {
      const data = await fetchAPI("/sessions");
      // Filter client-side if the API returns all sessions
      const repoSessions = data.filter((s: any) => s.repo_id === repoId);
      setSessions(repoSessions);
    } catch (e) {
      console.error("Failed to load sessions", e);
    }
  };

  const selectSession = async (sId: string) => {
    setSessionId(sId);
    try {
      // V2 Endpoint: GET /sessions/{id}/messages
      const history = await fetchAPI(`/sessions/${sId}/messages`);
      setMessages(history.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations
      })));
    } catch (e) {
      toast.error("Failed to load chat history");
    }
  };

  const handleDeleteSession = async (sId: string) => {
    // Stub: Optimistic update only since API endpoint is missing
    setSessions((prev) => prev.filter((s) => s.id !== sId));
    if (sessionId === sId) {
      setSessionId(null);
      setMessages([]);
    }
    toast.success("Session deleted");
  };

  // --- Ingestion ---
  const ingestRepo = async (url: string) => {
    if (!url) return;
    setIngestStatus("loading");
    const toastId = toast.loading("Syncing repository...");

    try {
      // FIX: Send JSON body { repo_url: url }
      // AND remove the query param ?url=...
      const data = await fetchAPI("/ingest", {
        method: "POST",
        body: JSON.stringify({ repo_url: url })
      });

      // ... existing polling logic ...
      const taskId = data.task_id;
      const interval = setInterval(async () => {
        try {
          const statusRes = await fetchAPI(`/ingest/${data.run_id}`); // Ensure this matches your route

          if (statusRes.status === "completed") { // Check your Enum string value
            clearInterval(interval);
            setIngestStatus("success");
            toast.success("Ready to chat!", { id: toastId });
            setRepoId(data.repo_id);
            // ... fetch structure ...
          } else if (statusRes.status === "failed") {
            clearInterval(interval);
            throw new Error(statusRes.error || "Ingestion failed");
          }
        } catch (e) {
          // Handle polling errors 
        }
      }, 2000);

    } catch (error: any) {
      setIngestStatus("error");
      toast.error(error.message || "Connection failed", { id: toastId });
    }
  };

  // --- Send Message ---
  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Optimistic UI Update
    const tempUserMsg: Message = { role: "user", content };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsChatting(true);

    try {
      let activeSessionId = sessionId;

      // 1. Create Session if needed
      if (!activeSessionId) {
        if (!repoId) throw new Error("No repository selected");
        const newSession = await fetchAPI("/sessions", {
          method: "POST",
          body: JSON.stringify({ repo_id: repoId })
        });
        activeSessionId = newSession.id;
        setSessionId(activeSessionId);
        loadSessions(); // Refresh list
      }

      // 2. Send Message (Backend handles saving)
      // V2 Endpoint: POST /sessions/{id}/messages
      const response = await fetchAPI(`/sessions/${activeSessionId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content })
      });

      // 3. Update UI with Real Response
      const aiMsg: Message = {
        id: response.id,
        role: "assistant",
        content: response.content,
        citations: response.citations
      };

      setMessages((prev) => [...prev, aiMsg]);

    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Failed to send message");
      // Remove optimistic message on failure
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsChatting(false);
    }
  };

  const fetchFileContent = async (repoId: string, filePath: string) => {
    // Stub: Return null or mock content since API is missing
    console.warn("fetchFileContent is a stub. Backend support needed.");
    return null;
  };

  return {
    messages,
    isChatting,
    ingestStatus,
    fileStructure,
    pinnedFiles,
    repoId,
    sessions,
    sessionId,
    selectSession,
    ingestRepo,
    sendMessage,
    // Helper to toggle pinned files
    togglePin: (file: string) => setPinnedFiles(p => p.includes(file) ? p.filter(f => f !== file) : [...p, file]),
    clearSession: () => { setSessionId(null); setMessages([]); },
    fetchFileContent,
    handleDeleteSession
  };
}