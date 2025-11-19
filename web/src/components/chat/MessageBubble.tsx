import React from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Bot, User, FileCode, Terminal } from "lucide-react";
import { motion } from "framer-motion";

interface MessageProps {
  role: string;
  content: string;
  sources?: string[];
}

export function MessageBubble({ role, content, sources }: MessageProps) {
  const isUser = role === "user";

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex w-full mb-8 ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`flex max-w-[85%] md:max-w-[75%] ${isUser ? "flex-row-reverse" : "flex-row"} gap-4`}>
        
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border shadow-sm ${
          isUser 
            ? "bg-primary text-primary-foreground border-primary" 
            : "bg-muted text-foreground border-border"
        }`}>
          {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
        </div>

        {/* Content */}
        <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} min-w-0`}>
          <div className={`px-5 py-4 rounded-2xl shadow-sm text-sm leading-7 ${
            isUser 
              ? "bg-primary text-primary-foreground rounded-tr-sm" 
              : "bg-card text-card-foreground border border-border rounded-tl-sm"
          }`}>
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || "");
                  return !inline && match ? (
                    <div className="rounded-md overflow-hidden my-3 border border-border/50 shadow-sm">
                      <div className="bg-zinc-950 text-zinc-400 text-xs px-3 py-1.5 flex items-center gap-2 border-b border-zinc-800">
                         <Terminal className="w-3 h-3"/> 
                         <span className="font-mono">{match[1]}</span>
                      </div>
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{ margin: 0, borderRadius: 0 }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    </div>
                  ) : (
                    <code className={`px-1.5 py-0.5 rounded font-mono text-xs ${
                      isUser ? "bg-primary-foreground/20" : "bg-muted text-foreground"
                    }`} {...props}>
                      {children}
                    </code>
                  );
                },
                // Style links and paragraphs
                a: ({node, ...props}) => <a {...props} className="underline underline-offset-4 font-medium" target="_blank" />,
                p: ({node, ...props}) => <p {...props} className="mb-3 last:mb-0" />,
                ul: ({node, ...props}) => <ul {...props} className="list-disc list-outside ml-4 mb-3 space-y-1" />,
                ol: ({node, ...props}) => <ol {...props} className="list-decimal list-outside ml-4 mb-3 space-y-1" />,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>

          {/* File Citations (Chips) */}
          {!isUser && sources && sources.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2 pl-1">
              {sources.map((source, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-[10px] font-medium text-muted-foreground bg-muted/50 px-2.5 py-1 rounded-full border border-border hover:bg-muted transition-colors cursor-default">
                  <FileCode className="w-3 h-3" />
                  <span className="truncate max-w-[200px]">{source}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}