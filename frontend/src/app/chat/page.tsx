"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, Sparkles, Terminal, Bug, FileCode } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";

// Components
import { MessageBubble } from "@/components/chat/MessageBubble";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { ChatInput } from "@/components/chat/ChatInput";
import { InspectorPanel } from "@/components/chat/InspectorPanel";
import { ThoughtChain } from "@/components/chat/ThoughtChain";
import { RepoPicker } from "@/components/chat/RepoPicker";

// Hooks
import { useCodeSense } from "@/hooks/use-codesense";
import { getCurrentUser } from "@/app/actions";
import type { components } from "@/lib/api/types";

interface Citation {
    file_path: string;
    symbol_name?: string;
    start_line?: number;
    content_preview?: string;
    score?: number;
}

const SUGGESTIONS = [
    { icon: Terminal, label: "Explain architecture", prompt: "Can you explain the high-level architecture of this codebase?" },
    { icon: Bug, label: "Find bugs", prompt: "Analyze the code for potential bugs or race conditions." },
    { icon: FileCode, label: "Add a feature", prompt: "I want to add a rate limiter. What files should I modify?" },
];

function ChatInterface() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const repoUrl = searchParams.get("url");

    // Layout
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [inspectorOpen, setInspectorOpen] = useState(false);

    // Data
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

    useEffect(() => {
        if (repoUrl && !hasInitialized.current) {
            hasInitialized.current = true;
            ingestRepo(repoUrl);
            getCurrentUser().then((u: any) => { if (u) setUser(u); });
        }
    }, [repoUrl, ingestRepo]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
    }, [messages, isChatting]);

    const handleCitationClick = async (citation: Citation) => {
        setInspectorOpen(true);
        setActiveFile({
            path: citation.file_path,
            content: citation.content_preview || "// Loading...",
            language: citation.file_path.split('.').pop() || 'text',
            startLine: citation.start_line || 1,
            endLine: (citation.start_line || 1) + 10
        });

        if (repoId) {
            const content = await fetchFileContent(repoId, citation.file_path);
            if (content) {
                setActiveFile({
                    path: citation.file_path,
                    content: content,
                    language: citation.file_path.split('.').pop() || 'text',
                    startLine: citation.start_line || 1,
                    endLine: (citation.start_line || 1) + 20
                });
            }
        }
    };

    const handleRepoIngest = (url: string) => {
        router.push(`/chat?url=${encodeURIComponent(url)}`);
        if (repoUrl !== url) hasInitialized.current = false;
    };

    return (
        <div className="fixed inset-0 top-16 z-0 flex w-full bg-background overflow-hidden">

            {/* Background Gradient */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-500/5 rounded-full blur-[100px] -z-10 pointer-events-none" />

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

            <main className="flex-1 flex flex-col h-full min-w-0 relative z-10">
                <header className="h-16 border-b border-border/40 flex items-center justify-between px-6 bg-background/50 backdrop-blur-md sticky top-0 z-20 shrink-0">
                    <RepoPicker
                        currentRepoUrl={repoUrl}
                        onIngest={handleRepoIngest}
                        isIngesting={ingestStatus === 'loading'}
                    />
                    {ingestStatus === 'loading' && (
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground animate-pulse bg-muted/50 px-3 py-1.5 rounded-full">
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Indexing...</span>
                        </div>
                    )}
                </header>

                <div className="flex-1 relative overflow-hidden flex flex-col min-h-0">
                    <ScrollArea className="h-full w-full">
                        <div className="max-w-7xl mx-auto py-10 px-4 md:px-4">

                            {messages.length === 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-6"
                                >
                                    <div className="w-16 h-16 bg-gradient-to-tr from-primary/10 to-blue-500/10 rounded-2xl flex items-center justify-center ring-1 ring-border/50">
                                        <Sparkles className="w-8 h-8 text-primary" />
                                    </div>
                                    <h2 className="text-2xl font-bold">How can I help you today?</h2>

                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full max-w-2xl">
                                        {SUGGESTIONS.map((s, i) => (
                                            <button
                                                key={i}
                                                onClick={() => sendMessage(s.prompt)}
                                                className="flex flex-col items-center gap-3 p-4 rounded-xl border border-border/50 bg-card/50 hover:bg-muted/50 hover:border-primary/20 transition-all text-center group"
                                            >
                                                <s.icon className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
                                                <span className="text-sm font-medium">{s.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </motion.div>
                            )}

                            <div className="flex flex-col pb-4">
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
                            </div>

                            <ThoughtChain isVisible={isChatting} />

                            <div ref={scrollRef} className="h-32" />
                        </div>
                    </ScrollArea>

                    {/* Chat Input Floating at bottom */}
                    <div className="absolute bottom-6 left-0 right-0 z-30 px-4 pointer-events-none">
                        <div className="max-w-3xl mx-auto pointer-events-auto">
                            <ChatInput
                                onSend={sendMessage}
                                disabled={ingestStatus !== 'success'}
                            />
                        </div>
                    </div>
                </div>
            </main>

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
        <Suspense fallback={null}>
            <ChatInterface />
        </Suspense>
    )
}