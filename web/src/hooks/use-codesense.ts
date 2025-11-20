// import { useState, useEffect, useCallback } from "react";
// import { toast } from "sonner";
// import { 
//     getOrCreateRepository, 
//     saveMessage, 
//     getChatSessions, 
//     getChatMessages,
//     deleteChatSession
// } from "@/app/actions";

// const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/['"]+/g, '');

// export interface Source {
//   file: string;
//   code: string;
//   start_line?: number;
//   end_line?: number;
//   repo_id?: string;
// }

// export interface Message {
//   role: "user" | "assistant";
//   content: string;
//   sources?: Source[];
// }

// export interface ChatSession {
//     id: string;
//     title: string | null;
//     updatedAt: Date;
// }

// export function useCodeSense() {
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [isChatting, setIsChatting] = useState(false);
//   const [ingestStatus, setIngestStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
//   const [contextFiles, setContextFiles] = useState<Source[]>([]);

//   const [repoId, setRepoId] = useState<string | null>(null); 
//   const [dbRepoId, setDbRepoId] = useState<string | null>(null);
//   const [sessionId, setSessionId] = useState<string | null>(null); 

//   const [fileStructure, setFileStructure] = useState<string[]>([]);
//   const [pinnedFiles, setPinnedFiles] = useState<string[]>([]);
//   const [sessions, setSessions] = useState<ChatSession[]>([]);

//   useEffect(() => {
//       if (dbRepoId) loadSessions(dbRepoId);
//   }, [dbRepoId]);

//   const loadSessions = async (rId: string) => {
//       const s = await getChatSessions(rId);
//       // @ts-ignore
//       setSessions(s);
//   };

//   const ingestRepo = async (url: string) => {
//     if (!url) return;
//     setIngestStatus("loading");
//     const toastId = toast.loading("Syncing repository...");

//     try {
//       const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(url)}`, { method: "POST" });
//       const data = await res.json();

//       const currentRepoId = data.repo_id;
//       setRepoId(currentRepoId);

//       const repoName = url.split("github.com/")[1] || "Repository";
//       const dbRepo = await getOrCreateRepository(url, repoName);
//       if (dbRepo) setDbRepoId(dbRepo.id);

//       const handleSuccess = async () => {
//           setIngestStatus("success");
//           toast.success("Ready to chat!", { id: toastId });
//           fetchFileStructure(currentRepoId);
//       };

//       if (data.status === "cached") {
//         handleSuccess();
//         return;
//       }

//       const taskId = data.task_id;
//       const interval = setInterval(async () => {
//         try {
//             const statusRes = await fetch(`${API_URL}/status/${taskId}`);
//             const statusData = await statusRes.json();
//             if (statusData.status === "SUCCESS") {
//               clearInterval(interval);
//               handleSuccess();
//             } else if (statusData.status === "FAILURE") {
//               clearInterval(interval);
//               setIngestStatus("error");
//               toast.error("Ingestion failed", { id: toastId });
//             }
//         } catch (e) { clearInterval(interval); }
//       }, 2000);

//     } catch (error) {
//       setIngestStatus("error");
//       toast.error("Connection failed", { id: toastId });
//     }
//   };

//   const startNewSession = () => {
//       // Just clear state. DB Session created only on first message.
//       setSessionId(null);
//       setMessages([]);
//   };

//   const selectSession = async (sId: string) => {
//       setSessionId(sId);
//       const msgs = await getChatMessages(sId);
//       const uiMsgs: Message[] = msgs.map(m => ({
//           role: m.role === "user" ? "user" : "assistant",
//           content: m.content
//       }));
//       setMessages(uiMsgs);
//   };

//   const handleDeleteSession = async (sId: string) => {
//       await deleteChatSession(sId);
//       if (sessionId === sId) {
//           setMessages([]);
//           setSessionId(null);
//       }
//       if (dbRepoId) loadSessions(dbRepoId);
//   };

//   const fetchFileStructure = async (id: string) => {
//       try {
//           const res = await fetch(`${API_URL}/repo/${id}/structure`);
//           const data = await res.json();
//           setFileStructure(data.files || []);
//       } catch (e) { console.error(e); }
//   };

//   const togglePin = (file: string) => {
//       setPinnedFiles(prev => 
//           prev.includes(file) ? prev.filter(f => f !== file) : [...prev, file]
//       );
//   };

//   const sendMessage = async (content: string) => {
//     if (!content.trim()) return;

//     const userMsg: Message = { role: "user", content };
//     setMessages(prev => [...prev, userMsg]);
//     setIsChatting(true);

//     // 1. Save User Message (Create Session if Needed)
//     let activeSessionId = sessionId;

//     if (dbRepoId) {
//         // If sessionId is null, this call creates it
//         const result = await saveMessage(sessionId, "user", content, dbRepoId);

//         if (result && 'error' in result && result.error === "LIMIT_REACHED") {
//              setIsChatting(false);
//              setMessages(prev => prev.slice(0, -1)); 
//              toast.error("Limit reached. Please login.");
//              return;
//         }

//         // FIX: Handle type mismatch by ensuring it's null if undefined
//         if (result && 'sessionId' in result) {
//             activeSessionId = result.sessionId ?? null; // <--- FIXED LINE
//             setSessionId(activeSessionId);
//             // Refresh list if this was a new session creation
//             if (!sessionId && dbRepoId) loadSessions(dbRepoId);
//         }
//     }

//     try {
//       // 2. Get AI Response
//       const response = await fetch(`${API_URL}/chat`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ 
//             message: content,
//             history: messages.map(m => ({ role: m.role, content: m.content })),
//             repo_id: repoId,
//             pinned_files: pinnedFiles
//         }),
//       });

//       const data = await response.json();
//       const aiContent = data.response || "Sorry, I encountered an error.";

//       setMessages((prev) => [...prev, { 
//             role: "assistant", 
//             content: aiContent, 
//             sources: data.context_used 
//       }]);

//       // 3. Save AI Message
//       if (activeSessionId) {
//           await saveMessage(activeSessionId, "assistant", aiContent);
//       }

//     } catch (error) {
//       toast.error("Network error sending message");
//       setMessages((prev) => [...prev, { role: "assistant", content: "Network error." }]);
//     } finally {
//       setIsChatting(false);
//     }
//   };

//   const fetchFileContent = async (rId: string, filePath: string): Promise<string | null> => {
//       try {
//           const res = await fetch(`${API_URL}/repo/${rId}/file?path=${encodeURIComponent(filePath)}`);
//           if (!res.ok) return null;
//           const data = await res.json();
//           return data.content;
//       } catch (e) { return null; }
//   };

//   const clearSession = () => {
//       startNewSession();
//   };

//   return {
//     messages,
//     isChatting,
//     ingestStatus,
//     contextFiles,
//     fileStructure,
//     pinnedFiles,
//     repoId,
//     sessions,
//     sessionId,
//     selectSession,
//     handleDeleteSession,
//     ingestRepo,
//     sendMessage,
//     fetchFileContent,
//     clearSession,
//     togglePin
//   };
// }


import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  getOrCreateRepository,
  saveMessage,
  getChatSessions,
  getChatMessages,
  deleteChatSession
} from "@/app/actions";

// --- Type Definitions ---
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

export interface ChatSession {
  id: string;
  title: string | null;
  updatedAt: Date;
}

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/['"]+/g, '');

export function useCodeSense() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [contextFiles, setContextFiles] = useState<Source[]>([]);

  const [repoId, setRepoId] = useState<string | null>(null);
  const [dbRepoId, setDbRepoId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const [fileStructure, setFileStructure] = useState<string[]>([]);
  const [pinnedFiles, setPinnedFiles] = useState<string[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  // --- Load Sessions on Repo Select ---
  useEffect(() => {
    if (dbRepoId) loadSessions(dbRepoId);
  }, [dbRepoId]);

  const loadSessions = async (rId: string) => {
    const s = await getChatSessions(rId);
    // @ts-ignore
    setSessions(s);
  };

  // --- Ingestion Logic ---
  const ingestRepo = async (url: string) => {
    if (!url) return;
    setIngestStatus("loading");
    const toastId = toast.loading("Syncing repository...");

    try {
      const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(url)}`, { method: "POST" });
      const data = await res.json();

      const currentRepoId = data.repo_id;
      setRepoId(currentRepoId);

      const repoName = url.split("github.com/")[1] || "Repository";
      const dbRepo = await getOrCreateRepository(url, repoName);
      if (dbRepo) setDbRepoId(dbRepo.id);

      const handleSuccess = async () => {
        setIngestStatus("success");
        toast.success("Ready to chat!", { id: toastId });
        fetchFileStructure(currentRepoId);
      };

      if (data.status === "cached") {
        handleSuccess();
        return;
      }

      const taskId = data.task_id;
      const interval = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_URL}/status/${taskId}`);
          const statusData = await statusRes.json();
          if (statusData.status === "SUCCESS") {
            clearInterval(interval);
            handleSuccess();
          } else if (statusData.status === "FAILURE") {
            clearInterval(interval);
            setIngestStatus("error");
            toast.error("Ingestion failed", { id: toastId });
          }
        } catch (e) { clearInterval(interval); }
      }, 2000);

    } catch (error) {
      setIngestStatus("error");
      toast.error("Connection failed", { id: toastId });
    }
  };

  const startNewSession = () => {
    setSessionId(null);
    setMessages([]);
  };

  const selectSession = async (sId: string) => {
    setSessionId(sId);
    const msgs = await getChatMessages(sId);
    const uiMsgs: Message[] = msgs.map(m => ({
      role: m.role === "user" ? "user" : "assistant",
      content: m.content
    }));
    setMessages(uiMsgs);
  };

  const handleDeleteSession = async (sId: string) => {
    await deleteChatSession(sId);
    if (sessionId === sId) {
      setMessages([]);
      setSessionId(null);
    }
    if (dbRepoId) loadSessions(dbRepoId);
  };

  const fetchFileStructure = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/repo/${id}/structure`);
      const data = await res.json();
      setFileStructure(data.files || []);
    } catch (e) { console.error(e); }
  };

  const togglePin = (file: string) => {
    setPinnedFiles(prev =>
      prev.includes(file) ? prev.filter(f => f !== file) : [...prev, file]
    );
  };

  // --- SEND MESSAGE (FIXED FOR DOUBLE LOADING) ---
  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // 1. Add User Message
    const userMsg: Message = { role: "user", content };
    setMessages(prev => [...prev, userMsg]);

    // Show "Thinking..." initially
    setIsChatting(true);

    // NOTE: We do NOT add the placeholder here anymore. 
    // We wait for the first stream chunk to arrive.

    // 2. Handle DB Session Creation
    let activeSessionId = sessionId;
    if (dbRepoId) {
      const result = await saveMessage(sessionId, "user", content, dbRepoId);

      if (result && 'error' in result && result.error === "LIMIT_REACHED") {
        setIsChatting(false);
        setMessages(prev => prev.slice(0, -1)); // Remove user msg
        toast.error("Limit reached. Please login.");
        return;
      }

      if (result && 'sessionId' in result) {
        activeSessionId = result.sessionId ?? null;
        setSessionId(activeSessionId);
        if (!sessionId && dbRepoId) loadSessions(dbRepoId);
      }
    }

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          history: messages.map(m => ({ role: m.role, content: m.content })),
          repo_id: repoId,
          pinned_files: pinnedFiles
        }),
      });

      if (!response.body) throw new Error("No response body");

      // 3. Handle Stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let aiFullContent = "";
      let buffer = "";
      let aiMessageCreated = false; // Track if we've added the bubble

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value, { stream: true });
        buffer += chunkValue;

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            // --- CRITICAL FIX: CREATE MESSAGE ON FIRST DATA ---
            if (!aiMessageCreated) {
              setMessages(prev => [...prev, { role: "assistant", content: "", sources: [] }]);
              aiMessageCreated = true;
              setIsChatting(false); // Hide "Thinking..." indicator now that bubble exists
            }

            const data = JSON.parse(line);

            if (data.type === "sources") {
              setMessages(prev => {
                const newArr = [...prev];
                const lastIdx = newArr.length - 1;
                if (newArr[lastIdx]) {
                  newArr[lastIdx] = { ...newArr[lastIdx], sources: data.data };
                }
                return newArr;
              });
            }
            else if (data.type === "chunk") {
              aiFullContent += data.content;
              setMessages(prev => {
                const newArr = [...prev];
                const lastIdx = newArr.length - 1;
                if (newArr[lastIdx]) {
                  newArr[lastIdx] = { ...newArr[lastIdx], content: aiFullContent };
                }
                return newArr;
              });
            }
          } catch (e) {
            console.error("Stream parse error", e);
          }
        }
      }

      if (activeSessionId) {
        await saveMessage(activeSessionId, "assistant", aiFullContent);
      }

    } catch (error) {
      console.error(error);
      toast.error("Network error sending message");

      // Handle error state
      setMessages((prev) => {
        // If bubble exists, update it
        if (prev[prev.length - 1]?.role === "assistant") {
          const newArr = [...prev];
          newArr[newArr.length - 1] = { ...newArr[newArr.length - 1], content: "Error: Could not fetch response." };
          return newArr;
        }
        // If bubble doesn't exist, add error message
        return [...prev, { role: "assistant", content: "Error: Could not fetch response.", sources: [] }];
      });

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
    startNewSession();
  };

  return {
    messages,
    isChatting,
    ingestStatus,
    contextFiles,
    fileStructure,
    pinnedFiles,
    repoId,
    sessions,
    sessionId,
    selectSession,
    handleDeleteSession,
    ingestRepo,
    sendMessage,
    fetchFileContent,
    clearSession,
    togglePin
  };
}