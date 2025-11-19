import { X, Copy, Check, Download, FileCode } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";

interface CodeViewerProps {
  isOpen: boolean;
  onClose: () => void;
  fileName: string;
  code: string;
  startLine?: number;
  endLine?: number;
}

export function CodeViewer({ isOpen, onClose, fileName, code, startLine = 1 }: CodeViewerProps) {
  const [copied, setCopied] = useState(false);

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

  // Parse Path for Breadcrumbs
  const pathParts = fileName.split('/');
  const fileNameOnly = pathParts.pop(); // remove last item (the file)
  
  const ext = fileName.split('.').pop() || 'text';
  const language = ext === 'ts' || ext === 'tsx' ? 'typescript' : 
                   ext === 'js' || ext === 'jsx' ? 'javascript' : 
                   ext === 'py' ? 'python' : 'text';

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 md:p-8">
          <motion.div 
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="bg-card w-full max-w-6xl h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden border border-border ring-1 ring-border"
          >
            {/* --- Modern Header with Breadcrumbs --- */}
            <div className="flex items-center justify-between px-6 py-3 bg-muted/30 border-b border-border select-none h-14 shrink-0">
              
              {/* Breadcrumbs */}
              <div className="flex items-center gap-3 overflow-hidden">
                 <div className="p-1.5 bg-primary/10 rounded-md shrink-0">
                    <FileCode className="w-4 h-4 text-primary" />
                 </div>
                 
                 <Breadcrumb>
                  <BreadcrumbList className="text-xs sm:text-sm font-medium">
                    {pathParts.map((part, i) => (
                      <div key={i} className="flex items-center">
                        <BreadcrumbItem>
                          <BreadcrumbLink className="hover:text-foreground transition-colors">{part}</BreadcrumbLink>
                        </BreadcrumbItem>
                        <BreadcrumbSeparator />
                      </div>
                    ))}
                    <BreadcrumbItem>
                      <BreadcrumbPage className="font-semibold text-foreground">{fileNameOnly}</BreadcrumbPage>
                    </BreadcrumbItem>
                  </BreadcrumbList>
                </Breadcrumb>
              </div>
              
              {/* Actions */}
              <div className="flex items-center gap-1">
                 <button 
                    onClick={handleDownload} 
                    className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                    title="Download"
                 >
                    <Download className="w-4 h-4" />
                 </button>
                 <button 
                    onClick={handleCopy} 
                    className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2"
                    title="Copy"
                 >
                    {copied ? <Check className="w-4 h-4 text-green-500"/> : <Copy className="w-4 h-4"/>}
                 </button>
                 
                 <div className="h-4 w-px bg-border mx-2" />
                 
                 <button 
                    onClick={onClose} 
                    className="p-2 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                 >
                    <X className="w-5 h-5" />
                 </button>
              </div>
            </div>

            {/* --- Code Area --- */}
            <div className="flex-1 overflow-auto custom-scrollbar bg-[#09090b] relative group">
               {/* Floating Language Badge */}
               <div className="absolute top-4 right-6 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <span className="text-[10px] font-mono font-bold text-zinc-500 bg-zinc-900/80 border border-zinc-800 px-2 py-1 rounded uppercase tracking-wider backdrop-blur-sm">
                    {language}
                  </span>
               </div>

               <SyntaxHighlighter
                  language={language}
                  style={vscDarkPlus}
                  startingLineNumber={startLine}
                  customStyle={{ 
                    margin: 0, 
                    padding: '2rem', 
                    background: 'transparent', 
                    fontSize: '13.5px', 
                    lineHeight: '1.6',
                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace"
                  }}
                  showLineNumbers={true}
                  lineNumberStyle={{ minWidth: "3.5em", paddingRight: "1.5em", color: "#52525b", textAlign: "right", userSelect: "none" }}
                  wrapLines={true}
               >
                  {code}
               </SyntaxHighlighter>
            </div>
            
            {/* Footer Info */}
            <div className="bg-muted/30 border-t border-border px-6 py-1.5 text-[10px] text-muted-foreground flex justify-between font-mono">
                <span>Lines {startLine} - {startLine + code.split('\n').length}</span>
                <span>UTF-8</span>
            </div>

          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}