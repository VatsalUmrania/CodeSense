import { useState, useEffect } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { motion, AnimatePresence } from "framer-motion";
import {
  Copy,
  Check,
  Download,
  Maximize2,
  Minimize2,
  X,
  FileCode2,
  WrapText,
  AlignLeft
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { fileIcons } from "@/config/fileIcons";

interface CodeViewerProps {
  isOpen: boolean;
  onClose: () => void;
  fileName: string;
  code: string;
  startLine?: number;
  endLine?: number;
  isFullFile?: boolean;
}

export function CodeViewer({
  isOpen,
  onClose,
  fileName,
  code,
  startLine = 1,
  endLine,
  isFullFile = false
}: CodeViewerProps) {
  const [copied, setCopied] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [wrapLines, setWrapLines] = useState(true);

  // Fallback for large files logic
  const lineCount = code ? code.split('\n').length : 0;
  const isActuallyFull = isFullFile || lineCount > 100;

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName.split('/').pop() || "code.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Language Detection
  const ext = fileName.split('.').pop()?.toLowerCase() || 'text';
  const languageMap: Record<string, string> = {
    ts: "typescript", tsx: "typescript", js: "javascript", jsx: "javascript",
    py: "python", rs: "rust", go: "go", html: "html", css: "css",
    json: "json", md: "markdown", yml: "yaml", yaml: "yaml", sql: "sql", java: "java",
  };

  const language = languageMap[ext] || 'text';
  // Use config icon or fallback
  const icon = fileIcons[language] || <FileCode2 className="w-4 h-4 text-blue-500" />;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-hidden">

          {/* Darker Backdrop for focus */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/40 backdrop-blur-[2px] transition-all"
          />

          {/* Modal Window */}
          <motion.div
            layout
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{
              opacity: 1,
              scale: 1,
              y: 0,
              width: isFullScreen ? "100%" : "auto",
              height: isFullScreen ? "100%" : "85vh",
              borderRadius: isFullScreen ? 0 : 12
            }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", damping: 25, stiffness: 350 }}
            className={cn(
              "relative flex flex-col bg-white shadow-2xl overflow-hidden min-w-[350px] sm:min-w-[700px] lg:min-w-[950px]",
              !isFullScreen && "ring-1 ring-black/5"
            )}
          >

            {/* --- Header --- */}
            <div
              className="flex items-center justify-between px-4 h-12 bg-white border-b border-zinc-100 shrink-0 select-none"
              onDoubleClick={() => setIsFullScreen(!isFullScreen)}
            >

              {/* Left: Window Controls */}
              <div className="flex items-center gap-2 w-[100px] group">
                <button onClick={onClose} className="w-3 h-3 rounded-full bg-[#FF5F57] border border-[#E0443E] flex items-center justify-center text-black/50 opacity-100 hover:opacity-80 transition-opacity">
                  <X className="w-2 h-2 opacity-0 group-hover:opacity-100" />
                </button>
                <button onClick={() => setIsFullScreen(!isFullScreen)} className="w-3 h-3 rounded-full bg-[#FEBC2E] border border-[#D89E24] flex items-center justify-center text-black/50 opacity-100 hover:opacity-80 transition-opacity">
                  {isFullScreen ? <Minimize2 className="w-2 h-2 opacity-0 group-hover:opacity-100" /> : <Maximize2 className="w-2 h-2 opacity-0 group-hover:opacity-100" />}
                </button>
                <div className="w-3 h-3 rounded-full bg-[#28C840] border border-[#1AAB29]" />
              </div>

              {/* Center: Filename */}
              <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
                <div className="opacity-80 scale-90">{icon}</div>
                <span className="text-[13px] font-medium text-zinc-700 tracking-tight">
                  {fileName.split('/').pop()}
                </span>
              </div>

              {/* Right: Actions */}
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn("h-7 w-7 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100", !wrapLines && "text-zinc-300")}
                  onClick={() => setWrapLines(!wrapLines)}
                  title="Toggle Word Wrap"
                >
                  <WrapText className="w-3.5 h-3.5" />
                </Button>

                <div className="h-3 w-px bg-zinc-200 mx-1" />

                <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100" onClick={handleCopy}>
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                </Button>

                <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100" onClick={handleDownload}>
                  <Download className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>

            {/* --- Code Content (Strictly Light Mode) --- */}
            <div className="flex-1 overflow-auto relative bg-[#fcfcfc] scroll-smooth">

              {/* Language Badge Sticky */}
              <div className="absolute top-3 right-4 z-10 pointer-events-none opacity-60 hover:opacity-100 transition-opacity">
                <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest font-mono select-none">
                  {language}
                </span>
              </div>

              <SyntaxHighlighter
                language={language}
                style={oneLight}
                startingLineNumber={isActuallyFull ? 1 : startLine}
                customStyle={{
                  margin: 0,
                  padding: '1.5rem',
                  background: 'transparent',
                  fontSize: '13px',
                  lineHeight: '1.6',
                  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                }}
                showLineNumbers={true}
                lineNumberStyle={{
                  minWidth: "3em",
                  paddingRight: "1.5em",
                  color: "#d4d4d8", // Zinc-300
                  textAlign: "right",
                  fontSize: '11px',
                  userSelect: "none"
                }}
                wrapLines={wrapLines}
                lineProps={(lineNumber) => {
                  const style: React.CSSProperties = { display: "block" };
                  // Highlight logic
                  if (isActuallyFull && startLine && endLine) {
                    if (lineNumber >= startLine && lineNumber <= endLine) {
                      style.backgroundColor = "#fffbeb"; // Amber-50 (Warm highlight)
                      style.borderLeft = "3px solid #fbbf24"; // Amber-400
                    }
                  }
                  return { style };
                }}
              >
                {code}
              </SyntaxHighlighter>
            </div>

            {/* --- Footer --- */}
            <div className="px-4 py-2 bg-white border-t border-zinc-100 flex justify-between items-center text-[10px] text-zinc-400 font-mono select-none">
              <div className="flex gap-4">
                <span className="flex items-center gap-1.5"><AlignLeft className="w-3 h-3" /> {lineCount} Lines</span>
                <span>{code.length.toLocaleString()} chars</span>
              </div>
              <div className="opacity-50">
                UTF-8
              </div>
            </div>

          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}