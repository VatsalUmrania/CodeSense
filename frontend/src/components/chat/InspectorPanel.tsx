import { useEffect, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { X, Download, Copy, Check, FileCode, Terminal, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface InspectorPanelProps {
  isOpen: boolean;
  onClose: () => void;
  file?: {
    path: string;
    content: string;
    language: string;
    startLine?: number;
    endLine?: number;
  } | null;
}

export function InspectorPanel({ isOpen, onClose, file }: InspectorPanelProps) {
  const [copied, setCopied] = useState(false);

  // Auto-scroll to the startLine when content loads
  useEffect(() => {
    if (file?.startLine && isOpen) {
        // Small timeout to allow DOM to render
        setTimeout(() => {
            const element = document.getElementById(`line-${file.startLine}`);
            element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 200);
    }
  }, [file, isOpen]);

  const handleCopy = () => {
    if (file?.content) {
      navigator.clipboard.writeText(file.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 450, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="h-full border-l border-border bg-background flex flex-col shadow-2xl z-20 shrink-0"
        >
          {/* Header */}
          <div className="h-14 flex items-center justify-between px-4 border-b border-border bg-muted/5">
            <div className="flex items-center gap-2 overflow-hidden">
              <FileCode className="w-4 h-4 text-primary" />
              <div className="flex flex-col min-w-0">
                 <span className="text-xs font-semibold truncate">{file?.path.split('/').pop()}</span>
                 <span className="text-[10px] text-muted-foreground truncate font-mono opacity-70">{file?.path}</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleCopy}>
                {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden relative bg-[#fafafa] dark:bg-[#0a0a0a]">
            {file ? (
                <ScrollArea className="h-full w-full">
                    <SyntaxHighlighter
                    language={file.language}
                    style={oneLight}
                    showLineNumbers={true}
                    startingLineNumber={1}
                    wrapLines={true}
                    customStyle={{ 
                        margin: 0, 
                        padding: '1.5rem', 
                        background: 'transparent',
                        fontSize: '12px',
                        fontFamily: 'var(--font-mono)'
                    }}
                    lineProps={(lineNumber) => {
                        const isHighlighted = file.startLine && file.endLine && lineNumber >= file.startLine && lineNumber <= file.endLine;
                        return {
                            id: `line-${lineNumber}`,
                            style: {
                                display: "block",
                                backgroundColor: isHighlighted ? "rgba(255, 200, 0, 0.1)" : undefined,
                                borderLeft: isHighlighted ? "2px solid #eab308" : "2px solid transparent",
                                width: "100%"
                            }
                        };
                    }}
                    >
                    {file.content}
                    </SyntaxHighlighter>
                </ScrollArea>
            ) : (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8 text-center">
                    <Terminal className="w-10 h-10 mb-4 opacity-20" />
                    <p className="text-sm">Select a citation to view context</p>
                </div>
            )}
          </div>

          {/* Footer */}
          <div className="h-8 border-t border-border flex items-center justify-between px-4 bg-muted/10 text-[10px] text-muted-foreground">
             <span>{file?.content.split('\n').length || 0} Lines</span>
             <span className="font-mono">{file?.language.toUpperCase()}</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}