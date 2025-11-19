"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronLeft, ChevronRight, Box } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { CodeViewer } from "@/components/chat/CodeViewer";
import { AppSidebar } from "@/components/layout/AppSidebar"; // <--- Import
import { RepoHeader } from "@/components/chat/RepoHeader";     // <--- Import
import { ChatInput } from "@/components/chat/ChatInput";       // <--- Import
import { useCodeSense, Source } from "@/hooks/use-codesense";

export default function ChatPage() {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [activeFile, setActiveFile] = useState<Source | null>(null);
  const [currentRepoUrl, setCurrentRepoUrl] = useState("");
  
  const { 
    messages, 
    isChatting, 
    ingestStatus, 
    contextFiles, 
    ingestRepo, 
    sendMessage, 
    clearSession 
  } = useCodeSense();

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isChatting]);

  const handleIngestWrapper = (url: string) => {
      setCurrentRepoUrl(url);
      ingestRepo(url);
  };

  const openFile = (filePath: string) => {
    let found = contextFiles.find(f => f.file === filePath);
    if (!found) {
      messages.forEach(m => {
        if (m.sources) {
          const s = m.sources.find(src => src.file === filePath);
          if (s) found = s;
        }
      });
    }
    if (found) setActiveFile(found);
  };

  return (
    <div className="flex h-screen w-full bg-background text-foreground font-sans overflow-hidden">
      
      <AppSidebar 
        isOpen={isSidebarOpen}
        repoUrl={currentRepoUrl}
        ingestStatus={ingestStatus}
        contextFiles={contextFiles}
        onClear={clearSession}
        onOpenFile={openFile}
      />

      <main className="flex-1 flex flex-col h-full min-w-0 bg-background relative">
        
        <button 
            onClick={() => setSidebarOpen(!isSidebarOpen)}
            className="absolute left-4 top-5 z-30 p-1.5 bg-background border border-border rounded-md shadow-sm hover:bg-accent text-muted-foreground"
        >
            {isSidebarOpen ? <ChevronLeft className="w-4 h-4"/> : <ChevronRight className="w-4 h-4"/>}
        </button>

        <RepoHeader onIngest={handleIngestWrapper} status={ingestStatus} />

        <div className="flex-1 overflow-hidden relative w-full">
            <ScrollArea className="h-full w-full">
                <div className="p-4 md:p-8 max-w-3xl mx-auto space-y-8 pb-6">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-[50vh] opacity-40 space-y-4">
                            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center">
                                <img src="/logo.svg" alt="Logo" className="w-8 h-8 opacity-50" />
                            </div>
                            <p className="text-muted-foreground font-medium">CodeSense AI</p>
                        </div>
                    )}
                    
                    {messages.map((msg, i) => (
                         <MessageBubble 
                            key={i} 
                            role={msg.role} 
                            content={msg.content} 
                            sources={msg.sources} 
                            onSourceClick={openFile}
                         />
                    ))}
                    
                    {isChatting && (
                        <div className="ml-14 flex gap-1">
                            <span className="w-2 h-2 bg-primary rounded-full animate-bounce"/>
                            <span className="w-2 h-2 bg-primary rounded-full animate-bounce delay-75"/>
                            <span className="w-2 h-2 bg-primary rounded-full animate-bounce delay-150"/>
                        </div>
                    )}
                    <div ref={scrollRef} className="h-1" />
                </div>
            </ScrollArea>
        </div>

        <ChatInput 
            onSend={sendMessage} 
            disabled={ingestStatus !== "success" && messages.length === 0} 
        />

        <CodeViewer 
            isOpen={!!activeFile} 
            onClose={() => setActiveFile(null)} 
            fileName={activeFile?.file || ""} 
            code={activeFile?.code || ""}
            startLine={activeFile?.start_line}
            endLine={activeFile?.end_line}
        />

      </main>
    </div>
  );
}