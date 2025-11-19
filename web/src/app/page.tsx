"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Loader2, Send, Github, Command, 
  FileCode2, Search, Box, ArrowRight
} from "lucide-react";
import { MessageBubble } from "@/components/chat/MessageBubble";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/['"]+/g, '');

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  const [repoUrl, setRepoUrl] = useState("");
  const [ingestStatus, setIngestStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [statusMsg, setStatusMsg] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isChatting]);

  const handleIngest = async () => {
    if (!repoUrl) return;
    setIngestStatus("loading");
    setStatusMsg("Cloning repository...");

    try {
      const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(repoUrl)}`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to start ingestion");
      
      const data = await res.json();
      const taskId = data.task_id;

      const interval = setInterval(async () => {
        const statusRes = await fetch(`${API_URL}/status/${taskId}`);
        const statusData = await statusRes.json();
        
        if (statusData.status === "SUCCESS") {
          clearInterval(interval);
          setIngestStatus("success");
          setStatusMsg("Repository indexed successfully.");
        } else if (statusData.status === "FAILURE") {
          clearInterval(interval);
          setIngestStatus("error");
          setStatusMsg(statusData.result?.message || "Ingestion failed.");
        } else {
          setStatusMsg("Indexing codebase...");
        }
      }, 2000);
    } catch (error: any) {
      setIngestStatus("error");
      setStatusMsg(error.message);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsChatting(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await response.json();
      
      if (data.response && data.response.startsWith("AI Error")) {
         setMessages((prev) => [...prev, { role: "assistant", content: "I'm having trouble connecting to the brain right now. Please try again." }]);
      } else {
         setMessages((prev) => [...prev, { role: "assistant", content: data.response, sources: data.context_used }]);
      }
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Network error. Please check your connection." }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden">
      
      {/* --- Sidebar (Using CSS Variable --sidebar) --- */}
      <aside className="w-72 bg-sidebar border-r border-sidebar-border hidden md:flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 h-16 flex items-center border-b border-sidebar-border">
          <div className="flex items-center gap-2 font-semibold text-sidebar-foreground">
            <div className="bg-primary/10 p-1.5 rounded-md">
              <Command className="w-5 h-5 text-primary" />
            </div>
            <span>CodeSense</span>
          </div>
        </div>
        
        {/* Sidebar Content */}
        <div className="flex-1 p-4 overflow-y-auto">
            <div className="mb-6">
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3 px-2">Active Repository</h3>
                
                <div className="space-y-1">
                    {ingestStatus === "success" ? (
                        <div className="group flex flex-col gap-2 p-3 rounded-lg bg-sidebar-accent/50 border border-sidebar-border hover:bg-sidebar-accent transition-all">
                            <div className="flex items-center gap-2">
                                <Box className="w-4 h-4 text-primary shrink-0" />
                                <span className="text-sm font-medium truncate text-sidebar-foreground">
                                    {repoUrl.split('/').pop() || "Repository"}
                                </span>
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-muted-foreground pl-6">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                <span>Index Active</span>
                            </div>
                        </div>
                    ) : (
                        <div className="p-3 rounded-lg border border-sidebar-border border-dashed flex items-center gap-2 text-muted-foreground bg-sidebar-accent/20">
                           <Search className="w-4 h-4" />
                           <span className="text-sm">No repo selected</span>
                        </div>
                    )}
                </div>
            </div>

            {/* "Files" Mockup (Since we don't have a list endpoint yet, we show instructions) */}
            <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3 px-2">Instructions</h3>
                <div className="space-y-1 text-sm text-sidebar-foreground/80 px-2">
                    <p className="flex items-start gap-2 py-1">
                        <span className="text-muted-foreground">1.</span> Paste GitHub URL above
                    </p>
                    <p className="flex items-start gap-2 py-1">
                        <span className="text-muted-foreground">2.</span> Click Import & Wait
                    </p>
                    <p className="flex items-start gap-2 py-1">
                        <span className="text-muted-foreground">3.</span> Ask questions about logic, bugs, or architecture
                    </p>
                </div>
            </div>
        </div>
        
        {/* Sidebar Footer */}
        <div className="p-4 border-t border-sidebar-border">
             <div className="flex items-center gap-3 px-2 py-2 rounded-md hover:bg-sidebar-accent cursor-pointer transition-colors">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs font-bold">
                    U
                </div>
                <div className="flex flex-col">
                    <span className="text-sm font-medium text-sidebar-foreground">User</span>
                    <span className="text-xs text-muted-foreground">Free Plan</span>
                </div>
             </div>
        </div>
      </aside>

      {/* --- Main Chat Area --- */}
      <main className="flex-1 flex flex-col min-w-0 bg-background">
        
        {/* Top Bar */}
        <header className="h-16 border-b border-border flex items-center justify-between px-6 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
          <div className="flex items-center gap-2 w-full max-w-2xl">
             <div className="relative flex-1 group">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors">
                    <Github className="w-4 h-4" />
                </div>
                <Input 
                    placeholder="Paste GitHub Repository URL (e.g., owner/repo)..." 
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    className="pl-9 h-9 bg-muted/40 border-transparent focus:bg-background focus:border-ring transition-all"
                    disabled={ingestStatus === "loading"}
                />
             </div>
             <Button 
                onClick={handleIngest} 
                disabled={ingestStatus === "loading"} 
                size="sm"
                className={ingestStatus === "success" ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}
             >
                {ingestStatus === "loading" ? (
                    <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin"/> Indexing</>
                ) : ingestStatus === "success" ? (
                    "Re-Import"
                ) : (
                    "Import"
                )}
             </Button>
          </div>
          
          {statusMsg && (
             <div className="hidden lg:flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
                {ingestStatus === "loading" && <Loader2 className="w-3 h-3 animate-spin" />}
                {statusMsg}
             </div>
          )}
        </header>

        {/* Scrollable Messages */}
        <ScrollArea className="flex-1 p-4 md:p-8">
          <div className="max-w-3xl mx-auto space-y-8 pb-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
                <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-2">
                    <FileCode2 className="w-8 h-8 text-primary" />
                </div>
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight">CodeSense</h2>
                    <p className="text-muted-foreground mt-1">Your AI-powered repository navigator.</p>
                </div>
                
                {ingestStatus === "success" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-8 w-full max-w-lg">
                        {["Explain the project structure", "Where is authentication handled?", "Identify potential security risks", "How do I run this locally?"].map((suggestion, i) => (
                            <button 
                                key={i}
                                onClick={() => { setInput(suggestion); handleSend(); }}
                                className="text-sm p-3 rounded-xl border border-border bg-card hover:bg-accent hover:text-accent-foreground text-left transition-colors flex items-center justify-between group"
                            >
                                {suggestion}
                                <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </button>
                        ))}
                    </div>
                )}
              </div>
            )}
            
            {messages.map((msg, i) => (
              <MessageBubble 
                key={i} 
                role={msg.role} 
                content={msg.content} 
                sources={msg.sources} 
              />
            ))}
            
            {isChatting && (
              <div className="flex items-center gap-2 text-muted-foreground text-sm ml-12 animate-pulse">
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-.3s]" />
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:-.5s]" />
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        {/* Input Footer */}
        <div className="p-4 border-t border-border bg-background">
          <div className="max-w-3xl mx-auto relative">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={ingestStatus === "success" ? "Ask a question about the codebase..." : "Import a repository to start chatting..."}
              className="pr-12 py-6 text-base shadow-sm border-border bg-muted/20 focus-visible:bg-background focus-visible:ring-1 focus-visible:ring-primary"
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={ingestStatus !== "success" && messages.length === 0} 
            />
            <Button 
              onClick={handleSend} 
              disabled={isChatting || (ingestStatus !== "success" && messages.length === 0)} 
              size="icon"
              className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 rounded-lg"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <div className="text-center mt-3">
             <p className="text-[10px] text-muted-foreground">
                AI can make mistakes. Check important info.
             </p>
          </div>
        </div>

      </main>
    </div>
  );
}