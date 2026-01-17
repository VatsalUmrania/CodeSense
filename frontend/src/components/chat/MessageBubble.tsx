import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check, Terminal, FileText, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
      className={cn("flex w-full mb-8 gap-4", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 shrink-0 border border-border mt-1">
        {isUser ? (
          <AvatarFallback className="bg-primary text-primary-foreground text-xs">{user?.email?.[0] || "U"}</AvatarFallback>
        ) : (
          <div className="w-full h-full bg-black flex items-center justify-center">
            <img src="/logo.svg" className="w-5 h-5" alt="AI" />
          </div>
        )}
      </Avatar>

      <div className={cn("flex flex-col max-w-[85%] lg:max-w-[75%] min-w-0", isUser ? "items-end" : "items-start")}>

        {/* User/AI Name Label */}
        <span className="text-[10px] font-medium text-muted-foreground mb-1 ml-1 opacity-70">
          {isUser ? "You" : "CodeSense"}
        </span>

        <div className={cn(
          "px-5 py-4 rounded-xl text-sm leading-7 shadow-sm border overflow-hidden break-words w-full",
          isUser
            ? "bg-primary text-primary-foreground border-primary"
            : "bg-card text-card-foreground border-border/60"
        )}>
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || "");
                const codeString = String(children).replace(/\n$/, "");
                return !inline && match ? (
                  <div className="rounded-md my-4 border border-border/40 bg-muted/30 overflow-hidden">
                    <div className="flex items-center justify-between px-3 py-1.5 bg-muted/50 border-b border-border/40">
                      <span className="font-mono text-[10px] text-muted-foreground">{match[1]}</span>
                      <button onClick={() => copyToClipboard(codeString)} className="hover:text-foreground text-muted-foreground">
                        {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                    <div className="overflow-x-auto w-full">
                      <SyntaxHighlighter
                        style={oneLight}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{ margin: 0, padding: '1rem', background: 'transparent', fontSize: '12px' }}
                        {...props}
                      >
                        {codeString}
                      </SyntaxHighlighter>
                    </div>
                  </div>
                ) : (
                  <code className="px-1.5 py-0.5 rounded bg-muted/50 font-mono text-[11px] border border-border/50" {...props}>
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
          <div className="mt-3 w-full grid grid-cols-1 sm:grid-cols-2 gap-2">
            {citations.map((cite, i) => (
              <button
                key={i}
                onClick={() => onCitationClick?.(cite)}
                className="flex items-center gap-3 p-2 rounded-lg border border-border/50 bg-background/50 hover:bg-accent/50 hover:border-primary/20 transition-all text-left group"
              >
                <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center shrink-0 group-hover:bg-background transition-colors border border-border/30">
                  <FileText className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                </div>
                <div className="flex flex-col min-w-0 flex-1">
                  <span className="text-xs font-medium truncate text-foreground/80 group-hover:text-primary">
                    {cite.file_path.split('/').pop()}
                  </span>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                    <span className="font-mono">L{cite.start_line}</span>
                    <span className="w-1 h-1 rounded-full bg-border" />
                    <span className="truncate opacity-70">
                      {cite.symbol_name || "Context"}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 -ml-2 transition-opacity" />
              </button>
            ))}
          </div>
        )}

      </div>
    </motion.div>
  );
}