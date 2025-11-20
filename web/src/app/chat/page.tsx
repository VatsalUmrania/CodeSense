// "use client";

// import { useState, useRef, useEffect, Suspense } from "react";
// import { useSearchParams, useRouter } from "next/navigation";
// import { ChevronLeft, ChevronRight, Home, Loader2, Share2 } from "lucide-react";
// import { ScrollArea } from "@/components/ui/scroll-area";
// import { MessageBubble } from "@/components/chat/MessageBubble";
// import { CodeViewer } from "@/components/chat/CodeViewer";
// import { AppSidebar } from "@/components/layout/AppSidebar";
// import { ChatInput } from "@/components/chat/ChatInput";
// import { useCodeSense, Source } from "@/hooks/use-codesense";
// import { Button } from "@/components/ui/button";
// import { toast } from "sonner";

// function ChatInterface() {
//   const searchParams = useSearchParams();
//   const router = useRouter();
//   const repoUrl = searchParams.get("url");

//   const [isSidebarOpen, setSidebarOpen] = useState(true);
//   const [activeFile, setActiveFile] = useState<Source | null>(null);
  
//   const { 
//     messages, 
//     isChatting, 
//     ingestStatus, 
//     contextFiles, 
//     ingestRepo, 
//     sendMessage,
//     fetchFileContent, // Ensure this is exported from your useCodeSense hook
//     clearSession 
//   } = useCodeSense();

//   const scrollRef = useRef<HTMLDivElement>(null);
//   const hasInitialized = useRef(false);

//   // 1. Auto-Ingest on Load
//   useEffect(() => {
//     if (repoUrl && !hasInitialized.current) {
//         hasInitialized.current = true;
//         ingestRepo(repoUrl);
//     } else if (!repoUrl) {
//         router.replace("/"); 
//     }
//   }, [repoUrl, ingestRepo, router]);

//   // 2. Auto-Scroll to bottom
//   useEffect(() => {
//     if (scrollRef.current) {
//         setTimeout(() => {
//             scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
//         }, 100);
//     }
//   }, [messages, isChatting]);

//   // 3. Handle File Opening (Fetches Full Content)
//   const openFile = async (filePath: string) => {
//     let foundSource = contextFiles.find(f => f.file === filePath);
    
//     // Fallback: search in message history if not in sidebar
//     if (!foundSource) {
//       messages.forEach(m => {
//         if (m.sources) {
//           const s = m.sources.find(src => src.file === filePath);
//           if (s) foundSource = s;
//         }
//       });
//     }

//     if (foundSource) {
//         // 1. Optimistic Open (Show the chunk we have immediately)
//         setActiveFile(foundSource);

//         // 2. Fetch Full Content in Background
//         if (foundSource.repo_id) {
//             const toastId = toast.loading("Fetching full file...");
            
//             const fullContent = await fetchFileContent(foundSource.repo_id, foundSource.file);
            
//             if (fullContent) {
//                 toast.dismiss(toastId);
//                 // Update state with full content
//                 setActiveFile({
//                     ...foundSource,
//                     code: fullContent,
//                     // We keep start/end_line to highlight the context
//                     start_line: foundSource.start_line, 
//                     end_line: foundSource.end_line
//                 });
//             } else {
//                 toast.dismiss(toastId);
//                 toast.error("Could not fetch full file. Showing context chunk only.");
//             }
//         }
//     } else {
//         toast.error("File reference not found.");
//     }
//   };

//   if (!repoUrl) return null;

//   return (
//     <div className="flex h-screen w-full bg-background text-foreground font-sans overflow-hidden selection:bg-primary/20">
      
//       <AppSidebar 
//         isOpen={isSidebarOpen}
//         repoUrl={repoUrl}
//         ingestStatus={ingestStatus}
//         messages={messages}
//         onClear={() => { clearSession(); router.push("/"); }}
//       />

//       <main className="flex-1 flex flex-col h-full min-w-0 relative bg-background/50">
        
//         {/* --- Header --- */}
//         <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-background/80 backdrop-blur-md shrink-0 z-20 sticky top-0">
//             <div className="flex items-center gap-3">
//                 <Button 
//                     variant="ghost" 
//                     size="icon" 
//                     onClick={() => setSidebarOpen(!isSidebarOpen)}
//                     className="text-muted-foreground hover:text-foreground h-8 w-8"
//                 >
//                     {isSidebarOpen ? <ChevronLeft className="w-4 h-4"/> : <ChevronRight className="w-4 h-4"/>}
//                 </Button>
                
//                 <div className="h-4 w-px bg-border mx-1" />
                
//                 <h1 className="text-sm font-medium text-foreground truncate max-w-[200px] sm:max-w-md">
//                     {repoUrl.replace("https://github.com/", "")}
//                 </h1>
//             </div>

//             <div className="flex items-center gap-1">
//                 {ingestStatus === "loading" && (
//                      <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary text-[10px] font-medium rounded-full mr-2">
//                         <Loader2 className="w-3 h-3 animate-spin" /> Syncing
//                     </div>
//                 )}
//             </div>
//         </header>

//         {/* --- Chat Area --- */}
//         <div className="flex-1 overflow-hidden relative w-full">
//             <ScrollArea className="h-full w-full">
//                 <div className="flex flex-col min-h-full p-4 md:p-8 max-w-7xl mx-auto">
                    
//                     {/* Empty State */}
//                     {messages.length === 0 && (
//                         <div className="flex-1 flex flex-col items-center justify-center opacity-0 animate-in fade-in slide-in-from-bottom-4 duration-700 fill-mode-forwards select-none min-h-[400px]">
//                             <div className="w-8 h-8 rounded-2xl bg-muted/50 flex items-center justify-center mb-4 ring-1 ring-border/50">
//                                 <img src="/logo.svg" alt="Logo" className="w-6 h-6 opacity-40 grayscale" />
//                             </div>
//                             <h2 className="text-xl font-semibold text-foreground/80">CodeSense AI</h2>
//                             <p className="text-sm text-muted-foreground mt-2">Context-aware repository chat</p>
//                         </div>
//                     )}
                    
//                     {/* Messages */}
//                     <div className="space-y-8">
//                         {messages.map((msg, i) => (
//                              <MessageBubble 
//                                 key={i} 
//                                 role={msg.role} 
//                                 content={msg.content} 
//                                 sources={msg.sources} 
//                                 onSourceClick={openFile}
//                              />
//                         ))}
//                     </div>
                    
//                     {/* Typing Indicator */}
//                     {isChatting && (
//                         <div className="flex items-center gap-3 mt-6 ml-1 animate-pulse">
//                              <div className="w-4 h-4 flex items-center justify-center">
//                                 <img src="/logo.svg" alt="Logo"/>
//                              </div>
//                              <span className="text-xs text-muted-foreground font-medium">Analyzing...</span>
//                         </div>
//                     )}
                    
//                     {/* Scroll Anchor (with padding for floating input) */}
//                     <div ref={scrollRef} className="w-full h-px mt-4 pb-32" />
//                 </div>
//             </ScrollArea>

//             {/* Floating Input */}
//             <ChatInput 
//                 onSend={sendMessage} 
//                 disabled={ingestStatus !== "success"} 
//             />
//         </div>

//         {/* --- Code Viewer Overlay --- */}
//         <CodeViewer 
//             isOpen={!!activeFile} 
//             onClose={() => setActiveFile(null)} 
//             fileName={activeFile?.file || ""} 
//             code={activeFile?.code || ""}
//             startLine={activeFile?.start_line}
//             endLine={activeFile?.end_line}
//             // Heuristic: if code is long, assume it's the full file
//             isFullFile={ (activeFile?.code?.length || 0) > 2000 } 
//         />

//       </main>
//     </div>
//   );
// }

// export default function ChatPage() {
//     return (
//         <Suspense fallback={<div className="flex h-screen items-center justify-center bg-background text-muted-foreground">Loading...</div>}>
//             <ChatInterface />
//         </Suspense>
//     )
// }

"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { CodeViewer } from "@/components/chat/CodeViewer";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatInput } from "@/components/chat/ChatInput";
import { useCodeSense, Source } from "@/hooks/use-codesense";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

function ChatInterface() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const repoUrl = searchParams.get("url");

  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [activeFile, setActiveFile] = useState<Source | null>(null);
  
  const { 
    messages, 
    isChatting, 
    ingestStatus, 
    contextFiles, 
    ingestRepo, 
    sendMessage,
    fetchFileContent,
    clearSession,
    // --- New Properties ---
    fileStructure,
    pinnedFiles,
    togglePin,
    repoId
  } = useCodeSense();

  const scrollRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  // 1. Auto-Ingest on Load
  useEffect(() => {
    if (repoUrl && !hasInitialized.current) {
        hasInitialized.current = true;
        ingestRepo(repoUrl);
    } else if (!repoUrl) {
        router.replace("/"); 
    }
  }, [repoUrl, ingestRepo, router]);

  // 2. Auto-Scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
        setTimeout(() => {
            scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
        }, 100);
    }
  }, [messages, isChatting]);

  // 3. Handle File Opening
  const openFile = async (filePath: string) => {
    // Try to find if we already have the chunk in context
    let foundSource = contextFiles.find(f => f.file === filePath);
    
    // Fallback: check message history
    if (!foundSource) {
      messages.forEach(m => {
        if (m.sources) {
          const s = m.sources.find(src => src.file === filePath);
          if (s) foundSource = s;
        }
      });
    }

    // If we found a chunk, start with that. Otherwise create a placeholder.
    const sourceToOpen: Source = foundSource || { 
        file: filePath, 
        code: "// Loading...", 
        repo_id: repoId || undefined 
    };

    setActiveFile(sourceToOpen);

    // Fetch Full Content in Background if we have a valid repo ID
    if (repoId) {
        const toastId = toast.loading("Fetching file...");
        const fullContent = await fetchFileContent(repoId, filePath);
        
        if (fullContent) {
            toast.dismiss(toastId);
            setActiveFile({
                ...sourceToOpen,
                code: fullContent,
                // Keep original lines if it was a chunk, otherwise default to full file
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

  return (
    <div className="flex h-screen w-full bg-background text-foreground font-sans overflow-hidden selection:bg-primary/20">
      
      <AppSidebar 
        isOpen={isSidebarOpen}
        repoUrl={repoUrl}
        ingestStatus={ingestStatus}
        messages={messages}
        // --- New Props Passed to Sidebar ---
        fileStructure={fileStructure}
        pinnedFiles={pinnedFiles}
        onTogglePin={togglePin}
        onFileClick={(file) => openFile(file)}
        onClear={() => { clearSession(); router.push("/"); }}
      />

      <main className="flex-1 flex flex-col h-full min-w-0 relative bg-background/50">
        
        {/* --- Header --- */}
        <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-background/80 backdrop-blur-md shrink-0 z-20 sticky top-0">
            <div className="flex items-center gap-3">
                <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => setSidebarOpen(!isSidebarOpen)}
                    className="text-muted-foreground hover:text-foreground h-8 w-8"
                >
                    {isSidebarOpen ? <ChevronLeft className="w-4 h-4"/> : <ChevronRight className="w-4 h-4"/>}
                </Button>
                
                <div className="h-4 w-px bg-border mx-1" />
                
                <h1 className="text-sm font-medium text-foreground truncate max-w-[200px] sm:max-w-md">
                    {repoUrl.replace("https://github.com/", "")}
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
                <div className="flex flex-col min-h-full p-4 md:p-8 max-w-7xl mx-auto">
                    
                    {/* Empty State */}
                    {messages.length === 0 && (
                        <div className="flex-1 flex flex-col items-center justify-center opacity-0 animate-in fade-in slide-in-from-bottom-4 duration-700 fill-mode-forwards select-none min-h-[400px]">
                            <div className="w-8 h-8 rounded-2xl bg-muted/50 flex items-center justify-center mb-4 ring-1 ring-border/50">
                                <img src="/logo.svg" alt="Logo" className="w-6 h-6 opacity-40 grayscale" />
                            </div>
                            <h2 className="text-xl font-semibold text-foreground/80">CodeSense AI</h2>
                            <p className="text-sm text-muted-foreground mt-2">Context-aware repository chat</p>
                        </div>
                    )}
                    
                    {/* Messages */}
                    <div className="space-y-8">
                        {messages.map((msg, i) => (
                             <MessageBubble 
                                key={i} 
                                role={msg.role} 
                                content={msg.content} 
                                sources={msg.sources} 
                                onSourceClick={openFile}
                             />
                        ))}
                    </div>
                    
                    {/* Typing Indicator */}
                    {isChatting && (
                        <div className="flex items-center gap-3 mt-6 ml-1 animate-pulse">
                             <div className="w-4 h-4 flex items-center justify-center">
                                <img src="/logo.svg" alt="Logo"/>
                             </div>
                             <span className="text-xs text-muted-foreground font-medium">Analyzing...</span>
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
            // Heuristic: if code is long, assume it's the full file
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