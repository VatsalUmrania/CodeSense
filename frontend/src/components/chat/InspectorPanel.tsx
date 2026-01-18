import { useEffect, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check, FileCode2, ArrowRightToLine, X } from "lucide-react";
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

  // Auto-scroll to the startLine
  useEffect(() => {
    if (file?.startLine && isOpen) {
      setTimeout(() => {
        const element = document.getElementById(`inspector-line-${file.startLine}`);
        element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 300);
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
          // Change: Animate width instead of X position to push content
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 500, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          // Change: Removed 'absolute' to participate in flex layout
          className="h-full border-l border-border bg-background shadow-xl z-20 shrink-0 flex flex-col overflow-hidden"
        >
          {/* Inner Container: Fixed width prevents content from squashing during animation */}
          <div className="w-[500px] flex flex-col h-full">

            {/* Header */}
            <div className="h-14 flex items-center justify-between px-4 border-b border-border bg-muted/20 backdrop-blur-sm shrink-0">
              <div className="flex items-center gap-2.5 overflow-hidden">
                <div className="p-1.5 bg-primary/10 rounded-md">
                  <FileCode2 className="w-4 h-4 text-primary" />
                </div>
                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-semibold truncate text-foreground">{file?.path.split('/').pop()}</span>
                  <span className="text-[10px] text-muted-foreground truncate font-mono opacity-70 max-w-[250px]">{file?.path}</span>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleCopy} title="Copy Content">
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5 text-muted-foreground" />}
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-destructive/10 hover:text-destructive transition-colors" onClick={onClose}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Content - Forced Light Mode */}
            <div className="flex-1 overflow-hidden relative bg-[#fafafa]">
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
                      lineHeight: '1.6',
                      fontFamily: "'JetBrains Mono', monospace"
                    }}
                    lineNumberStyle={{
                      minWidth: "2.5em",
                      paddingRight: "1em",
                      color: "#a1a1aa",
                      fontSize: '11px'
                    }}
                    lineProps={(lineNumber) => {
                      const isHighlighted = file.startLine && file.endLine && lineNumber >= file.startLine && lineNumber <= file.endLine;
                      return {
                        id: `inspector-line-${lineNumber}`,
                        style: {
                          display: "block",
                          backgroundColor: isHighlighted ? "rgba(234, 179, 8, 0.15)" : undefined,
                          borderLeft: isHighlighted ? "3px solid #eab308" : "3px solid transparent",
                          width: "100%"
                        }
                      };
                    }}
                  >
                    {file.content}
                  </SyntaxHighlighter>
                </ScrollArea>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-8 text-center bg-zinc-50">
                  <div className="w-12 h-12 rounded-full bg-zinc-100 border border-zinc-200 flex items-center justify-center mb-4">
                    <FileCode2 className="w-6 h-6 opacity-30" />
                  </div>
                  <p className="text-sm font-medium">No file selected</p>
                  <p className="text-xs opacity-60 mt-1">Click on a citation in the chat to view context.</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="h-8 border-t border-border flex items-center justify-between px-4 bg-zinc-50 text-[10px] text-zinc-400 select-none shrink-0">
              <span>{file?.content.split('\n').length || 0} lines</span>
              <span className="font-mono font-medium">{file?.language.toUpperCase() || 'TEXT'}</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}