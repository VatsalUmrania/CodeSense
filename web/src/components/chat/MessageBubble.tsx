import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check, FileText, ChevronDown, BookOpen, Terminal } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface MessageProps {
  role: string;
  content: string;
  sources?: { file: string; code: string }[];
  user?: { email: string } | null;
  onSourceClick?: (file: string) => void;
}

export function MessageBubble({ role, content, sources, user, onSourceClick }: MessageProps) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const displaySources = isExpanded ? sources : sources?.slice(0, 3);
  const remainingCount = (sources?.length || 0) - 3;

  const userInitial = user?.email?.[0]?.toUpperCase() || "U";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex w-full mb-8 gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="w-8 h-8 shrink-0 flex items-center justify-center mt-1">
          <img src="/logo.svg" alt="AI" className="w-8 h-8" />
        </div>
      )}

      <div className={cn(
        "flex flex-col max-w-[85%] md:max-w-[75%]",
        isUser ? "items-end" : "items-start"
      )}>

        <div className={cn(
          "px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-sm",
          isUser
            ? "bg-primary text-primary-foreground rounded-tr-sm"
            : "bg-card border border-border text-card-foreground rounded-tl-sm"
        )}>
          <ReactMarkdown
            components={{
              // --- NEW: Custom Link Renderer to Open Files ---
              a({ node, href, children, ...props }) {
                return (
                  <span
                    onClick={() => href && onSourceClick?.(href)}
                    className="text-primary hover:underline cursor-pointer font-medium inline-flex items-center gap-1"
                    title={`Open ${href}`}
                  >
                    <FileText className="w-3 h-3 inline" />
                    {children}
                  </span>
                );
              },
              // -----------------------------------------------
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || "");
                const codeString = String(children).replace(/\n$/, "");

                return !inline && match ? (
                  <div className="rounded-md overflow-hidden my-3 border border-border/50 shadow-sm bg-secondary">
                    <div className="flex items-center justify-between px-3 py-1.5 bg-primary-foreground border-b border-[#333] text-primary-foreground">
                      <div className="flex items-center gap-2">
                        <Terminal className="w-3 h-3 opacity-50" />
                        <span className="font-mono text-[10px] opacity-70">{match[1]}</span>
                      </div>
                      <button onClick={() => copyToClipboard(codeString)}>
                        {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3 opacity-50 hover:opacity-100" />}
                      </button>
                    </div>
                    <SyntaxHighlighter
                      style={oneLight}
                      language={match[1]}
                      PreTag="div"
                      customStyle={{ margin: 0, padding: '1rem', fontSize: '12px' }}
                      {...props}
                    >
                      {codeString}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code className={cn(
                    "px-1 py-0.5 rounded font-mono text-[11px]",
                    isUser ? "bg-primary-foreground/20" : "bg-muted text-foreground"
                  )} {...props}>
                    {children}
                  </code>
                );
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* References Section */}
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-3 w-full animate-in fade-in slide-in-from-top-2 duration-500">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">References</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {displaySources?.map((source, idx) => (
                <button
                  key={idx}
                  onClick={() => onSourceClick?.(source.file)}
                  className="group flex items-center gap-2 text-xs text-left bg-card hover:bg-accent/50 border border-border p-2 rounded-lg transition-all hover:shadow-sm hover:border-primary/30"
                >
                  <div className="p-1.5 bg-muted rounded-md group-hover:bg-background transition-colors">
                    <FileText className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary" />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="truncate font-medium text-foreground/80 group-hover:text-primary">
                      {source.file.split('/').pop()}
                    </span>
                    <span className="truncate text-[10px] text-muted-foreground opacity-70">
                      {source.file}
                    </span>
                  </div>
                </button>
              ))}
            </div>

            {remainingCount > 0 && !isExpanded && (
              <button
                onClick={() => setIsExpanded(true)}
                className="mt-2 text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 font-medium ml-1"
              >
                Show {remainingCount} more <ChevronDown className="w-3 h-3" />
              </button>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 shrink-0 border border-primary/20 mt-1">
          <AvatarImage src="" />
          <AvatarFallback className="bg-primary text-primary-foreground text-xs font-bold">
            {userInitial}
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  );
}