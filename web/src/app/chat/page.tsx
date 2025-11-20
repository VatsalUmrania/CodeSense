"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, Sparkles, Terminal, ShieldAlert, FileCode } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { CodeViewer } from "@/components/chat/CodeViewer";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatInput } from "@/components/chat/ChatInput";
import { useCodeSense, Source } from "@/hooks/use-codesense";
import { toast } from "sonner";
import { getCurrentUser } from "@/app/actions";

function ChatInterface() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const repoUrl = searchParams.get("url");

  // Sidebar State
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true);
  const [activeFile, setActiveFile] = useState<Source | null>(null);
  const [user, setUser] = useState<{ email: string } | null>(null);
  
  const { 
    messages, 
    isChatting, 
    ingestStatus, 
    contextFiles, 
    ingestRepo, 
    sendMessage,
    fetchFileContent,
    clearSession,
    repoId,
    sessions,
    sessionId,
    selectSession,
    handleDeleteSession
  } = useCodeSense();

  const scrollRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  // 1. Auto-Ingest & Auth
  useEffect(() => {
    if (repoUrl && !hasInitialized.current) {
        hasInitialized.current = true;
        ingestRepo(repoUrl);
        getCurrentUser().then((u: any) => { if (u) setUser(u); });
    } else if (!repoUrl) {
        router.replace("/"); 
    }
  }, [repoUrl, ingestRepo, router]);

  // 2. Auto-Scroll
  useEffect(() => {
    if (scrollRef.current) {
        setTimeout(() => {
            scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
        }, 100);
    }
  }, [messages, isChatting]);

  // 3. File Handling
  const openFile = async (filePath: string) => {
    let foundSource = contextFiles.find(f => f.file === filePath);
    if (!foundSource) {
      messages.forEach(m => {
        if (m.sources) {
          const s = m.sources.find(src => src.file === filePath);
          if (s) foundSource = s;
        }
      });
    }

    const sourceToOpen: Source = foundSource || { file: filePath, code: "// Loading...", repo_id: repoId || undefined };
    setActiveFile(sourceToOpen);

    if (repoId) {
        const toastId = toast.loading("Fetching file...");
        const fullContent = await fetchFileContent(repoId, filePath);
        if (fullContent) {
            toast.dismiss(toastId);
            setActiveFile({
                ...sourceToOpen,
                code: fullContent,
                start_line: foundSource ? foundSource.start_line : undefined, 
                end_line: foundSource ? foundSource.end_line : undefined
            });
        } else {
            toast.dismiss(toastId);
            if (!foundSource) {
                toast.error("Could not fetch file content.");
                setActiveFile(null);
            } else {
                toast.warning("Full content unavailable. Showing snippet.");
            }
        }
    }
  };

  if (!repoUrl) return null;

  const suggestions = [
      { icon: <Terminal className="w-4 h-4 text-blue-500"/>, text: "Explain the project structure" },
      { icon: <ShieldAlert className="w-4 h-4 text-red-500"/>, text: "Identify security vulnerabilities" },
      { icon: <FileCode className="w-4 h-4 text-emerald-500"/>, text: "Generate a README.md" },
      { icon: <Sparkles className="w-4 h-4 text-amber-500"/>, text: "Suggest performance improvements" },
  ];

  return (
    <div className="flex h-screen w-full bg-background text-foreground font-sans overflow-hidden selection:bg-primary/20">
      
      <AppSidebar 
        isCollapsed={!isSidebarExpanded}
        toggleSidebar={() => setIsSidebarExpanded(!isSidebarExpanded)}
        repoUrl={repoUrl}
        sessions={sessions}
        currentSessionId={sessionId}
        onSessionSelect={selectSession}
        onSessionDelete={handleDeleteSession}
        onClear={() => clearSession()}
      />

      <main className="flex-1 flex flex-col h-full min-w-0 relative bg-background/50">
        
        {/* --- Header --- */}
        <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-background/80 backdrop-blur-md shrink-0 z-20 sticky top-0">
            <div className="flex items-center gap-3 pl-2">
                <h1 className="text-sm font-medium text-foreground truncate max-w-[200px] sm:max-w-md flex items-center gap-2">
                   <span className="opacity-50">/</span> {repoUrl.replace("https://github.com/", "")}
                </h1>
            </div>

            <div className="flex items-center gap-1">
                {ingestStatus === "loading" && (
                     <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary text-[10px] font-medium rounded-full mr-2">
                        <Loader2 className="w-3 h-3 animate-spin" /> Syncing
                    </div>
                )}
            </div>
        </header>

        {/* --- Chat Area --- */}
        <div className="flex-1 overflow-hidden relative w-full">
            <ScrollArea className="h-full w-full">
                <div className="flex flex-col min-h-full p-4 md:p-8 max-w-5xl mx-auto">
                    
                    {/* --- EMPTY STATE --- */}
                    {messages.length === 0 && (
                        <div className="flex-1 flex flex-col items-center justify-center h-full min-h-[60vh] animate-in fade-in slide-in-from-bottom-4 duration-700">
                            
                            <div className="relative mb-8 group cursor-default">
                                <div className="absolute -inset-1 bg-linear-to-r from-primary/30 to-purple-500/30 rounded-full blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>
                                <img src="/logo.svg" alt="CodeSense" className="w-10 h-10 opacity-90" />
                            </div>

                            <h2 className="text-2xl font-semibold text-foreground tracking-tight mb-3">
                                CodeSense AI
                            </h2>
                            <p className="text-muted-foreground text-sm max-w-md text-center leading-relaxed mb-10">
                                I've indexed <span className="font-medium text-foreground">{repoUrl.split('/').pop()}</span>. <br/>
                                Ask me anything about the codebase, architecture, or bugs.
                            </p>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl px-4">
                                {suggestions.map((s, i) => (
                                    <button 
                                        key={i}
                                        onClick={() => sendMessage(s.text)}
                                        className="flex items-center gap-3 p-4 text-sm text-left bg-card border border-border/60 rounded-xl hover:bg-accent/50 hover:border-primary/20 hover:shadow-sm transition-all group"
                                    >
                                        <div className="p-2 bg-background rounded-lg border border-border/50 text-muted-foreground group-hover:text-foreground transition-colors">
                                            {s.icon}
                                        </div>
                                        <span className="text-muted-foreground group-hover:text-foreground transition-colors">
                                            {s.text}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {/* Messages */}
                    <div className="space-y-8 pb-4">
                        {messages.map((msg, i) => (
                             <MessageBubble 
                                key={i} 
                                role={msg.role} 
                                content={msg.content} 
                                sources={msg.sources} 
                                user={user}
                                onSourceClick={openFile}
                             />
                        ))}
                    </div>
                    
                    {/* Typing Indicator */}
                    {isChatting && (
                        <div className="flex items-center gap-3 mt-2 ml-1">     
                            <img src="logo.svg" className="w-6 h-6 animate-spin text-muted-foreground" />
                            <span className="text-xs text-muted-foreground animate-pulse">Thinking...</span>
                        </div>
                    )}
                    
                    {/* Scroll Anchor */}
                    <div ref={scrollRef} className="w-full h-px mt-4 pb-32" />
                </div>
            </ScrollArea>

            {/* Floating Input */}
            <ChatInput 
                onSend={sendMessage} 
                disabled={ingestStatus !== "success"} 
            />
        </div>

        {/* --- Code Viewer Overlay --- */}
        <CodeViewer 
            isOpen={!!activeFile} 
            onClose={() => setActiveFile(null)} 
            fileName={activeFile?.file || ""} 
            code={activeFile?.code || ""}
            startLine={activeFile?.start_line}
            endLine={activeFile?.end_line}
            isFullFile={ (activeFile?.code?.length || 0) > 2000 } 
        />

      </main>
    </div>
  );
}

export default function ChatPage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center bg-background text-muted-foreground">Loading...</div>}>
            <ChatInterface />
        </Suspense>
    )
}