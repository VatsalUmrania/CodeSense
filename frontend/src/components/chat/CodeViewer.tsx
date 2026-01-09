import { useState, useEffect, JSX } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { duotoneLight, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { motion, AnimatePresence } from "framer-motion";
import { 
  SiTypescript, 
  SiJavascript, 
  SiPython, 
  SiRust, 
  SiGo, 
  SiHtml5, 
  SiCss3, 
  SiJson,
  SiMarkdown,
  SiBabel,
  SiYaml,
  SiDocker,
  SiTailwindcss,
  SiReact,
  SiVuedotjs,
  SiNextdotjs,
} from "react-icons/si";
import { RiNodejsFill } from "react-icons/ri";
import { 
  X, 
  Copy, 
  Check, 
  Download, 
  FileCode, 
  Maximize2, 
  Minimize2, 
  Terminal,
  Eye
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

  // Detect if it's a large file (fallback logic)
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
  const languageMap: Record<string, string> ={
    ts: "typescript",
    tsx: "typescript",
    js: "javascript",
    jsx: "javascript",
    py: "python",
    rs: "rust",
    go: "go",
    html: "html",
    css: "css",
    json: "json",
    md: "markdown",
    yml: "yaml",
    yaml: "yaml",
  };

  const language = languageMap[ext] || 'text';

  const DefaultIcon = <FileCode className="w-4 h-4 text-primary" />;
  const icon = fileIcons[language] || DefaultIcon;


  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          
          {/* Backdrop */}
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-background/60 backdrop-blur-sm"
          />

          {/* Modal Container */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ 
                opacity: 1, 
                scale: 1, 
                y: 0,
                width: isFullScreen ? "100%" : "100%",
                height: isFullScreen ? "100%" : "85vh",
                maxWidth: isFullScreen ? "100%" : "1200px"
            }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className={cn(
                "relative flex flex-col overflow-hidden bg-background/95 border border-border/50 shadow-2xl z-50",
                isFullScreen ? "rounded-none inset-0" : "rounded-xl ring-1 ring-white/5"
            )}
          >
            
            {/* --- Header --- */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border/40 bg-muted/20 shrink-0">
              
              <div className="flex items-center gap-3 overflow-hidden">
                 <div className="p-2 shrink-0">
                    {icon}
                 </div>
                 <div className="flex flex-col min-w-0">
                    <span className="text-sm font-medium text-foreground truncate">
                        {fileName.split('/').pop()}
                    </span>
                    <span className="text-[10px] text-muted-foreground truncate font-mono opacity-80">
                        {fileName}
                    </span>
                 </div>
              </div>
              
              <div className="flex items-center gap-1 sm:gap-2">
                 <div className="hidden sm:flex items-center bg-background/50 border border-border/50 rounded-lg p-0.5 mr-2">
                     <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleCopy} title="Copy Code">
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-500"/> : <Copy className="w-3.5 h-3.5"/>}
                     </Button>
                     <div className="w-px h-3 bg-border/50 mx-0.5" />
                     <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleDownload} title="Download File">
                        <Download className="w-3.5 h-3.5" />
                     </Button>
                 </div>

                 <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsFullScreen(!isFullScreen)}>
                    {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                 </Button>

                 <Button variant="ghost" size="icon" className="h-8 w-8 hover:text-destructive" onClick={onClose}>
                    <X className="w-5 h-5" />
                 </Button>
              </div>
            </div>

            {/* --- Code Content --- */}
            <div className="flex-1 overflow-auto relative bg-white custom-scrollbar">
               <div className="absolute top-4 right-6 z-10 pointer-events-none">
                  <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-[10px] font-mono text-zinc-400 backdrop-blur-sm">
                    <Terminal className="w-3 h-3" />
                    {language}
                  </span>
               </div>

               <SyntaxHighlighter
                  language={language}
                  style={oneLight}
                  // If it's a full file, start counting from 1. If it's a snippet, use the chunk's start line.
                  startingLineNumber={isActuallyFull ? 1 : startLine}
                  customStyle={{ 
                    margin: 0, 
                    padding: '2rem', 
                    background: 'transparent', 
                    fontSize: '13px', 
                    lineHeight: '1.6',
                    fontFamily: "var(--font-geist-mono), monospace",
                  }}
                  showLineNumbers={true}
                  lineNumberStyle={{ 
                      minWidth: "3.5em", 
                      paddingRight: "1.5em", 
                      color: "#52525b", 
                      textAlign: "right",
                      fontSize: '11px'
                  }}
                  wrapLines={true}
                  lineProps={(lineNumber) => {
                      const style: React.CSSProperties = { display: "block" };
                      
                      // Only highlight if we are in Full File mode and have a valid range
                      if (isActuallyFull && startLine && endLine) {
                          if (lineNumber >= startLine && lineNumber <= endLine) {
                            style.backgroundColor = "color-mix(in srgb, var(--primary) 15%, transparent)";
                            style.borderLeft = "3px solid var(--primary)";
                          }
                      }
                      return { style };
                  }}
               >
                  {code}
               </SyntaxHighlighter>
            </div>
            
            {/* --- Footer --- */}
            <div className="px-4 py-1.5 bg-muted/30 border-t border-border/40 flex justify-between items-center text-[10px] text-muted-foreground font-mono select-none">
                <div className="flex gap-4">
                    <span>{lineCount} Lines</span>
                    <span>UTF-8</span>
                    <span>{code.length} chars</span>
                </div>
            </div>

          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}