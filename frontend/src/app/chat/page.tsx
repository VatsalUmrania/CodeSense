"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

// Components
import { MessageBubble } from "@/components/chat/MessageBubble";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatInput } from "@/components/chat/ChatInput";
import { InspectorPanel } from "@/components/chat/InspectorPanel";
import { ThoughtChain } from "@/components/chat/ThoughtChain";
import { RepoPicker } from "@/components/chat/RepoPicker";

// Hooks & Actions
import { useCodeSense } from "@/hooks/use-codesense";
import { getCurrentUser } from "@/app/actions";
import type { components } from "@/lib/api/types";

// Types
interface Citation {
    file_path: string;
    symbol_name?: string;
    start_line?: number;
    content_preview?: string;
    score?: number;
}

function ChatInterface() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const repoUrl = searchParams.get("url");

    // --- Layout State ---
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [inspectorOpen, setInspectorOpen] = useState(false);

    // --- Data State ---
    const [user, setUser] = useState<{ email: string } | null>(null);
    const [activeFile, setActiveFile] = useState<{
        path: string;
        content: string;
        language: string;
        startLine?: number;
        endLine?: number;
    } | null>(null);

    const {
        messages,
        isChatting,
        ingestStatus,
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

    // 1. Initialization
    useEffect(() => {
        if (repoUrl && !hasInitialized.current) {
            hasInitialized.current = true;
            ingestRepo(repoUrl);
            getCurrentUser().then((u: any) => { if (u) setUser(u); });
        } else if (!repoUrl) {
            // Optional: Redirect or just allow picking a repo
        }
    }, [repoUrl, ingestRepo]);

    // 2. Auto-Scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    }, [messages, isChatting]);

    // 3. Handle Citation Click
    const handleCitationClick = async (citation: Citation) => {
        setInspectorOpen(true);
        // Optimistic / Loading State
        setActiveFile({
            path: citation.file_path,
            content: citation.content_preview || "// Loading full content...",
            language: citation.file_path.split('.').pop() || 'text',
            startLine: citation.start_line || 1,
            endLine: (citation.start_line || 1) + 10 // approximate
        });

        if (repoId) {
            const content = await fetchFileContent(repoId, citation.file_path);
            if (content) {
                setActiveFile({
                    path: citation.file_path,
                    content: content,
                    language: citation.file_path.split('.').pop() || 'text',
                    startLine: citation.start_line || 1,
                    endLine: (citation.start_line || 1) + 20 // Highlight range
                });
            }
        }
    };

    const handleRepoIngest = (url: string) => {
        router.push(`/chat?url=${encodeURIComponent(url)}`);
        if (repoUrl !== url) {
            hasInitialized.current = false; // Reset init check for new repo
        }
    };

    return (
        // FIX: Use fixed positioning to anchor below the 64px (h-16) header
        <div className="fixed inset-0 top-16 z-0 flex w-full bg-background overflow-hidden font-sans">

            {/* Ambient Background Glow - Matching Landing Page */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] -z-10 pointer-events-none" />
            <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-[100px] -z-10 pointer-events-none" />

            {/* 1. Left Sidebar */}
            <AppSidebar
                isCollapsed={isSidebarCollapsed}
                toggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                repoUrl={repoUrl || ""}
                sessions={sessions}
                currentSessionId={sessionId}
                onSessionSelect={selectSession}
                onSessionDelete={handleDeleteSession}
                onClear={() => clearSession()}
            />

            {/* 2. Main Chat Canvas */}
            <main className="flex-1 flex flex-col h-full min-w-0 relative z-10">

                {/* Header inside chat */}
                <header className="h-14 border-b border-border/40 flex items-center justify-between px-6 bg-background/40 backdrop-blur-md sticky top-0 z-20 shrink-0">
                    <RepoPicker
                        currentRepoUrl={repoUrl}
                        onIngest={handleRepoIngest}
                        isIngesting={ingestStatus === 'loading'}
                    />
                    {ingestStatus === 'loading' && (
                        <div className="flex items-center gap-2 text-[10px] text-muted-foreground animate-pulse">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            Indexing Codebase...
                        </div>
                    )}
                </header>

                {/* Chat Stream */}
                {/* FIX: added min-h-0 to ensure flex child shrinks properly */}
                <div className="flex-1 relative overflow-hidden flex flex-col min-h-0">
                    {/* FIX: Enforce h-full on ScrollArea */}
                    <ScrollArea className="h-full w-full">
                        <div className="max-w-3xl mx-auto py-10 px-6">

                            {/* Welcome State */}
                            {messages.length === 0 && (
                                <div className="flex flex-col items-center justify-center min-h-[40vh] text-center space-y-4 opacity-0 animate-in fade-in duration-700 slide-in-from-bottom-4 fill-mode-forwards">
                                    <div className="w-16 h-16 bg-linear-to-tr from-primary/20 to-blue-500/20 rounded-2xl flex items-center justify-center mb-4 ring-1 ring-border/50">
                                        <img src="/logo.svg" className="w-8 h-8 " />
                                    </div>
                                    <h2 className="text-2xl font-semibold tracking-tight">CodeSense IDE</h2>
                                    <p className="text-muted-foreground max-w-md text-sm leading-relaxed">
                                        Context-aware chat for <strong>{repoUrl?.split('/').pop() || 'your codebase'}</strong>.
                                        <br />I can explain architecture, find bugs, and write code.
                                    </p>
                                </div>
                            )}

                            {/* Message List */}
                            {messages.map((msg, i) => (
                                <MessageBubble
                                    key={i}
                                    role={msg.role}
                                    content={msg.content}
                                    citations={msg.citations}
                                    user={user}
                                    onCitationClick={handleCitationClick}
                                />
                            ))}

                            {/* Thought Process */}
                            <ThoughtChain isVisible={isChatting} />

                            {/* Bottom Spacer */}
                            <div ref={scrollRef} className="h-4" />
                        </div>
                    </ScrollArea>

                    {/* Input Area */}
                    <div className="p-6 pt-2 bg-linear-to-t from-background via-background to-transparent z-20 shrink-0">
                        <div className="max-w-3xl mx-auto">
                            <ChatInput
                                onSend={sendMessage}
                                disabled={ingestStatus !== 'success'}
                            />
                        </div>
                    </div>
                </div>

            </main>

            {/* 3. Right Inspector Panel */}
            <InspectorPanel
                isOpen={inspectorOpen}
                onClose={() => setInspectorOpen(false)}
                file={activeFile}
            />

        </div>
    );
}

export default function ChatPage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center text-sm text-muted-foreground">Loading CodeSense...</div>}>
            <ChatInterface />
        </Suspense>
    )
}