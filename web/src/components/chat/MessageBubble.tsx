import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { User, Terminal, Copy, Check, FileCode, ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface MessageProps {
  role: string;
  content: string;
  sources?: { file: string; code: string }[];
  onSourceClick?: (file: string) => void;
}

export function MessageBubble({ role, content, sources, onSourceClick }: MessageProps) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false); // State for "Show More"

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Logic to slice the sources
  const hasSources = sources && sources.length > 0;
  const displaySources = isExpanded ? sources : sources?.slice(0, 2);
  const hiddenCount = (sources?.length || 0) - 2;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex w-full mb-8 ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`flex max-w-[90%] md:max-w-[80%] ${isUser ? "flex-row-reverse" : "flex-row"} gap-4`}>
        
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border shadow-sm ${
          isUser 
            ? "bg-primary text-primary-foreground border-primary" 
            : "bg-card text-card-foreground border-border"
        }`}>
          {isUser ? <User className="w-4 h-4" /> : <img src="/logo.svg" alt="AI" className="w-5 h-5" />}
        </div>

        {/* Content Bubble */}
        <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} min-w-0 w-full`}>
          <div className={`px-5 py-4 rounded-2xl shadow-sm text-sm leading-7 w-full ${
            isUser 
              ? "bg-primary text-primary-foreground rounded-tr-sm" 
              : "bg-card text-card-foreground border border-border rounded-tl-sm"
          }`}>
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || "");
                  const codeString = String(children).replace(/\n$/, "");
                  
                  return !inline && match ? (
                    <div className="rounded-lg overflow-hidden my-4 border border-border/40 shadow-sm group">
                      <div className="bg-zinc-950 text-zinc-400 text-xs px-3 py-2 flex items-center justify-between border-b border-zinc-800">
                         <div className="flex items-center gap-2">
                           <Terminal className="w-3 h-3 text-blue-400"/> 
                           <span className="font-mono text-zinc-300">{match[1]}</span>
                         </div>
                         <button 
                            onClick={() => copyToClipboard(codeString)}
                            className="hover:text-white transition-colors"
                         >
                            {copied ? <Check className="w-3 h-3 text-green-500"/> : <Copy className="w-3 h-3"/>}
                         </button>
                      </div>
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{ margin: 0, borderRadius: 0, fontSize: '13px' }}
                        {...props}
                      >
                        {codeString}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className={`px-1.5 py-0.5 rounded font-mono text-xs border ${
                      isUser 
                        ? "bg-primary-foreground/20 border-primary-foreground/30" 
                        : "bg-muted text-foreground border-border"
                    }`} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {content}
            </ReactMarkdown>
          </div>

          {/* --- REFERENCES SECTION (Cleaned Up) --- */}
          {!isUser && hasSources && (
            <div className="mt-3 w-full animate-in fade-in duration-500">
              <div className="flex flex-wrap gap-2 items-center">
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-bold mr-2">
                   Context:
                </span>
                
                <AnimatePresence initial={false}>
                    {displaySources?.map((source, idx) => (
                    <motion.button
                        key={idx}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        onClick={() => onSourceClick?.(source.file)}
                        className="group flex items-center gap-1.5 text-xs text-foreground bg-card hover:bg-accent hover:text-accent-foreground px-2.5 py-1 rounded-md border border-border transition-all hover:border-primary/40"
                        title={source.file}
                    >
                        <FileCode className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary" />
                        <span className="truncate max-w-[180px] font-mono opacity-80">
                            {source.file.split('/').pop()} 
                        </span>
                    </motion.button>
                    ))}
                </AnimatePresence>

                {/* The +X More Button */}
                {!isExpanded && hiddenCount > 0 && (
                    <button 
                        onClick={() => setIsExpanded(true)}
                        className="flex items-center gap-1 text-[10px] font-medium text-muted-foreground bg-muted/30 px-2 py-1 rounded-md hover:bg-muted transition-colors"
                    >
                        +{hiddenCount}
                        <ChevronDown className="w-3 h-3" />
                    </button>
                )}

                {/* Collapse Button */}
                {isExpanded && (
                    <button 
                        onClick={() => setIsExpanded(false)}
                        className="flex items-center gap-1 text-[10px] font-medium text-muted-foreground hover:text-primary transition-colors ml-1"
                    >
                        Show less <ChevronUp className="w-3 h-3" />
                    </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}