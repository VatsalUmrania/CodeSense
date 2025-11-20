// import { useState } from "react";
// import { toast } from "sonner";

// const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/['"]+/g, '');

// export interface Source {
//   file: string;
//   code: string;
//   start_line?: number;
//   end_line?: number;
//   repo_id?: string; // <--- Added
// }

// export interface Message {
//   role: "user" | "assistant";
//   content: string;
//   sources?: Source[];
// }

// export function useCodeSense() {
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [isChatting, setIsChatting] = useState(false);
//   const [ingestStatus, setIngestStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
//   const [contextFiles, setContextFiles] = useState<Source[]>([]);

//   const ingestRepo = async (url: string) => {
//     if (!url) return;
//     setIngestStatus("loading");
//     const toastId = toast.loading("Cloning repository...");

//     try {
//       const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(url)}`, { method: "POST" });
//       const data = await res.json();
      
//       if (data.status === "cached") {
//         setIngestStatus("success");
//         toast.success("Loaded from cache!", { id: toastId });
//         return;
//       }

//       const taskId = data.task_id;
//       const interval = setInterval(async () => {
//         try {
//             const statusRes = await fetch(`${API_URL}/status/${taskId}`);
//             const statusData = await statusRes.json();
            
//             if (statusData.status === "SUCCESS") {
//               clearInterval(interval);
//               setIngestStatus("success");
//               toast.success("Ready to chat!", { id: toastId });
//             } else if (statusData.status === "FAILURE") {
//               clearInterval(interval);
//               setIngestStatus("error");
//               toast.error("Ingestion failed", { id: toastId });
//             }
//         } catch (e) {
//             clearInterval(interval);
//         }
//       }, 2000);

//     } catch (error) {
//       setIngestStatus("error");
//       toast.error("Connection failed", { id: toastId });
//     }
//   };

//   const sendMessage = async (content: string) => {
//     if (!content.trim()) return;

//     const userMsg: Message = { role: "user", content };
    
//     // Optimistic UI update
//     const newHistory = [...messages, userMsg];
//     setMessages(newHistory);
//     setIsChatting(true);

//     try {
//       // Prepare history payload (exclude the current new message from history as it's sent as 'message')
//       // We strip out 'sources' to keep the payload light
//       const historyPayload = messages.map(m => ({
//         role: m.role,
//         content: m.content
//       }));

//       const response = await fetch(`${API_URL}/chat`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ 
//             message: content,
//             history: historyPayload // <--- Send History
//         }),
//       });
      
//       const data = await response.json();
      
//       if (data.response && data.response.startsWith("AI Error")) {
//          toast.error("AI Brain connection failed");
//          setMessages((prev) => [...prev, { role: "assistant", content: "I'm having trouble connecting. Please try again." }]);
//       } else {
//          if (data.context_used) {
//             const newSources = data.context_used as Source[];
//             setContextFiles(prev => {
//                 const existing = new Set(prev.map(p => p.file));
//                 const unique = newSources.filter(s => !existing.has(s.file));
//                 return [...prev, ...unique];
//             });
//          }
         
//          setMessages((prev) => [...prev, { 
//             role: "assistant", 
//             content: data.response, 
//             sources: data.context_used 
//          }]);
//       }
//     } catch (error) {
//       toast.error("Network error sending message");
//       setMessages((prev) => [...prev, { role: "assistant", content: "Network error." }]);
//     } finally {
//       setIsChatting(false);
//     }
//   };

//   // --- NEW: Fetch Full File ---
//   const fetchFileContent = async (repoId: string, filePath: string): Promise<string | null> => {
//       try {
//           const res = await fetch(`${API_URL}/repo/${repoId}/file?path=${encodeURIComponent(filePath)}`);
//           if (!res.ok) return null;
//           const data = await res.json();
//           return data.content;
//       } catch (e) {
//           console.error(e);
//           return null;
//       }
//   };

//   const clearSession = () => {
//       setMessages([]);
//       setContextFiles([]);
//   };

//   return {
//     messages,
//     isChatting,
//     ingestStatus,
//     contextFiles,
//     ingestRepo,
//     sendMessage,
//     fetchFileContent, // <--- Export this
//     clearSession
//   };
// }

import { useState, useEffect } from "react";
import { toast } from "sonner";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/['"]+/g, '');

export interface Source {
  file: string;
  code: string;
  start_line?: number;
  end_line?: number;
  repo_id?: string;
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
  const [repoId, setRepoId] = useState<string | null>(null); // Store Repo ID
  
  // --- NEW STATE ---
  const [fileStructure, setFileStructure] = useState<string[]>([]);
  const [pinnedFiles, setPinnedFiles] = useState<string[]>([]);

  const ingestRepo = async (url: string) => {
    if (!url) return;
    setIngestStatus("loading");
    const toastId = toast.loading("Cloning repository...");

    try {
      const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(url)}`, { method: "POST" });
      const data = await res.json();
      
      const currentRepoId = data.repo_id;
      setRepoId(currentRepoId);

      if (data.status === "cached") {
        setIngestStatus("success");
        toast.success("Loaded from cache!", { id: toastId });
        fetchFileStructure(currentRepoId); // Fetch tree
        return;
      }

      const taskId = data.task_id;
      const interval = setInterval(async () => {
        try {
            const statusRes = await fetch(`${API_URL}/status/${taskId}`);
            const statusData = await statusRes.json();
            
            if (statusData.status === "SUCCESS") {
              clearInterval(interval);
              setIngestStatus("success");
              toast.success("Ready to chat!", { id: toastId });
              setRepoId(statusData.result.repo_id);
              fetchFileStructure(statusData.result.repo_id); // Fetch tree
            } else if (statusData.status === "FAILURE") {
              clearInterval(interval);
              setIngestStatus("error");
              toast.error("Ingestion failed", { id: toastId });
            }
        } catch (e) {
            clearInterval(interval);
        }
      }, 2000);

    } catch (error) {
      setIngestStatus("error");
      toast.error("Connection failed", { id: toastId });
    }
  };

  // Fetch Tree
  const fetchFileStructure = async (id: string) => {
      try {
          const res = await fetch(`${API_URL}/repo/${id}/structure`);
          const data = await res.json();
          setFileStructure(data.files || []);
      } catch (e) {
          console.error("Failed to fetch file structure", e);
      }
  };

  const togglePin = (file: string) => {
      setPinnedFiles(prev => 
          prev.includes(file) ? prev.filter(f => f !== file) : [...prev, file]
      );
  };

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMsg: Message = { role: "user", content };
    setMessages([...messages, userMsg]);
    setIsChatting(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            message: content,
            history: messages.map(m => ({ role: m.role, content: m.content })),
            repo_id: repoId,      // Pass Repo ID
            pinned_files: pinnedFiles // Pass Pins
        }),
      });
      
      const data = await response.json();
      
      if (data.response && data.response.startsWith("AI Error")) {
         toast.error("AI Brain connection failed");
         setMessages((prev) => [...prev, { role: "assistant", content: "Connection error." }]);
      } else {
         if (data.context_used) {
            // ... context handling logic ...
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

  const fetchFileContent = async (rId: string, filePath: string): Promise<string | null> => {
      try {
          const res = await fetch(`${API_URL}/repo/${rId}/file?path=${encodeURIComponent(filePath)}`);
          if (!res.ok) return null;
          const data = await res.json();
          return data.content;
      } catch (e) { return null; }
  };

  const clearSession = () => {
      setMessages([]);
      setContextFiles([]);
      setPinnedFiles([]);
  };

  return {
    messages,
    isChatting,
    ingestStatus,
    contextFiles,
    fileStructure, // Export
    pinnedFiles,   // Export
    repoId,
    ingestRepo,
    sendMessage,
    fetchFileContent,
    clearSession,
    togglePin      // Export
  };
}