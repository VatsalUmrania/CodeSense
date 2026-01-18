import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check, FileText, ChevronRight, User, Bot } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { components } from "@/lib/api/types";

// Type alias for easier usage
type ChunkCitation = components["schemas"]["ChunkCitation"];

interface MessageProps {
  role: string;
  content: string;
  citations?: ChunkCitation[];
  user?: { email: string } | null;
  onCitationClick?: (citation: ChunkCitation) => void;
}

export function MessageBubble({ role, content, citations, user, onCitationClick }: MessageProps) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn("flex w-full mb-6 gap-4", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <Avatar className={cn(
        "h-8 w-8 shrink-0 mt-1 border",
        isUser ? "border-primary/20" : "border-border bg-muted/50"
      )}>
        {isUser ? (
          <AvatarFallback className="bg-primary text-primary-foreground text-xs font-medium">
            {user?.email?.[0]?.toUpperCase() || <User className="w-4 h-4" />}
          </AvatarFallback>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-white dark:bg-zinc-900">
            {/* Using an icon instead of img to prevent broken image links if logo is missing */}
            <Bot className="w-5 h-5 text-blue-500" />
          </div>
        )}
      </Avatar>

      <div className={cn("flex flex-col max-w-[85%] lg:max-w-[75%] min-w-0", isUser ? "items-end" : "items-start")}>

        {/* Name Label */}
        <span className="text-[11px] text-muted-foreground mb-1.5 ml-1 font-medium opacity-60">
          {isUser ? "You" : "CodeSense AI"}
        </span>

        <div className={cn(
          "px-5 py-4 rounded-2xl text-[15px] leading-7 shadow-sm border w-full overflow-hidden",
          isUser
            ? "bg-primary text-primary-foreground border-primary rounded-tr-sm"
            : "bg-card text-card-foreground border-border/50 rounded-tl-sm"
        )}>
          <ReactMarkdown
            components={{
              // 1. Fix Paragraph Spacing
              p: ({ children }) => <p className="mb-4 last:mb-0 leading-7">{children}</p>,

              // 2. Fix List Spacing
              ul: ({ children }) => <ul className="list-disc pl-6 mb-4 space-y-1.5">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-6 mb-4 space-y-1.5">{children}</ol>,
              li: ({ children }) => <li className="pl-1">{children}</li>,

              // 3. Headings
              h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>,
              h2: ({ children }) => <h2 className="text-lg font-semibold mb-3 mt-4">{children}</h2>,
              h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-3">{children}</h3>,

              // 4. Blockquotes
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-primary/30 pl-4 py-1 my-4 bg-muted/20 italic rounded-r">
                  {children}
                </blockquote>
              ),

              // 5. Code Blocks - FORCED LIGHT THEME
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || "");
                const codeString = String(children).replace(/\n$/, "");

                if (!inline && match) {
                  return (
                    <div className="rounded-lg my-5 border border-zinc-200 overflow-hidden shadow-sm bg-[#fafafa] group/code relative z-10">
                      {/* Header */}
                      <div className="flex items-center justify-between px-3 py-2 bg-white border-b border-zinc-200">
                        <div className="flex gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
                          <div className="w-2.5 h-2.5 rounded-full bg-yellow-400/80" />
                          <div className="w-2.5 h-2.5 rounded-full bg-green-400/80" />
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-wider">{match[1]}</span>
                          <button
                            onClick={() => copyToClipboard(codeString)}
                            className="p-1 hover:bg-zinc-100 rounded transition-colors text-zinc-400 hover:text-zinc-600"
                            title="Copy code"
                          >
                            {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </div>

                      {/* Code Area - Forced Light Mode */}
                      <div className="overflow-x-auto w-full">
                        <SyntaxHighlighter
                          style={oneLight}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{
                            margin: 0,
                            padding: '1.25rem',
                            background: 'transparent', // Let container bg show through
                            fontSize: '13px',
                            lineHeight: '1.6',
                            fontFamily: 'JetBrains Mono, Menlo, monospace',
                          }}
                          {...props}
                        >
                          {codeString}
                        </SyntaxHighlighter>
                      </div>
                    </div>
                  );
                }

                // Inline Code
                return (
                  <code
                    className={cn(
                      "px-1.5 py-0.5 rounded font-mono text-[13px] font-medium mx-0.5",
                      isUser
                        ? "bg-white/20 text-white"
                        : "bg-zinc-100 text-zinc-800 border border-zinc-200"
                    )}
                    {...props}
                  >
                    {children}
                  </code>
                );
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* --- CITATIONS GRID --- */}
        {!isUser && citations && citations.length > 0 && (
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 w-full animate-in fade-in slide-in-from-top-2 duration-500">
            {citations.map((cite, i) => (
              <button
                key={i}
                onClick={() => onCitationClick?.(cite)}
                className="flex items-center gap-3 p-2.5 rounded-lg border border-border/50 bg-background/40 hover:bg-accent/50 hover:border-primary/20 hover:shadow-sm transition-all text-left group"
              >
                <div className="h-8 w-8 rounded-md bg-muted/50 flex items-center justify-center shrink-0 border border-border/20 group-hover:bg-background group-hover:text-primary transition-colors">
                  <FileText className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-[11px] font-medium truncate text-foreground/80 group-hover:text-primary transition-colors">
                    {cite.file_path.split('/').pop()}
                  </span>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground/60">
                    <span className="font-mono">L{cite.start_line}</span>
                    <span className="w-0.5 h-0.5 rounded-full bg-border" />
                    <span className="truncate opacity-80 max-w-[120px]">
                      {cite.symbol_name || "Context"}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 -ml-1 transition-all" />
              </button>
            ))}
          </div>
        )}

      </div>
    </motion.div>
  );
}