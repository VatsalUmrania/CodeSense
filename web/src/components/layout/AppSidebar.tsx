import { motion } from "framer-motion";
import { Github, FileText, Trash2, Layers, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Source } from "@/hooks/use-codesense";

interface SidebarProps {
  isOpen: boolean;
  repoUrl: string;
  ingestStatus: string;
  contextFiles: Source[];
  onClear: () => void;
  onOpenFile: (file: string) => void;
}

export function AppSidebar({ isOpen, repoUrl, ingestStatus, contextFiles, onClear, onOpenFile }: SidebarProps) {
  return (
    <motion.aside 
      initial={{ width: 260 }}
      animate={{ width: isOpen ? 260 : 0 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="bg-sidebar border-r border-sidebar-border hidden md:flex flex-col shrink-0 h-full overflow-hidden z-30"
    >
      {/* Header */}
      <div className="p-4 h-16 flex items-center border-b border-sidebar-border shrink-0 bg-sidebar/50 backdrop-blur-sm">
        <div className="flex items-center gap-3 font-bold text-sidebar-foreground tracking-tight px-2">
          <div className="w-7 h-7 bg-primary/10 rounded-lg flex items-center justify-center">
             <img src="/logo.svg" alt="CodeSense" className="w-4 h-4" />
          </div>
          <span className="whitespace-nowrap text-sm">CodeSense</span>
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col p-4 space-y-6">
          
          {/* 1. Repository Card */}
          <div className="space-y-2 shrink-0">
              <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider px-1">Repository</h3>
              <div className="p-3 rounded-lg border border-sidebar-border bg-sidebar-accent/40 hover:bg-sidebar-accent/60 transition-colors group">
                  <div className="flex items-center gap-2 text-sidebar-foreground overflow-hidden">
                      <Github className="w-3.5 h-3.5 shrink-0 text-muted-foreground group-hover:text-foreground transition-colors" />
                      <span className="text-xs font-medium truncate">
                          {repoUrl ? repoUrl.split("github.com/")[1] : "No Repo"}
                      </span>
                  </div>
                  {ingestStatus === "success" && (
                       <div className="flex items-center gap-1.5 text-[10px] text-emerald-600 dark:text-emerald-400 mt-2 pl-0.5">
                          <div className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                          Synced
                       </div>
                  )}
              </div>
          </div>

          <Separator className="bg-sidebar-border" />

          {/* 2. Context Files (Scrollable) */}
          <div className="flex-1 flex flex-col min-h-0">
              <div className="flex items-center justify-between mb-2 px-1 shrink-0">
                  <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Context</h3>
                  <span className="text-[10px] bg-sidebar-accent px-1.5 py-0.5 rounded-md text-sidebar-foreground font-mono">
                      {contextFiles.length}
                  </span>
              </div>
              
              <ScrollArea className="flex-1 -mx-2 px-2">
                  <div className="space-y-0.5 pb-2">
                    {contextFiles.map((source, i) => (
                        <button 
                            key={i} 
                            onClick={() => onOpenFile(source.file)}
                            className="w-full group flex items-center gap-2.5 p-2 rounded-md hover:bg-sidebar-accent transition-colors text-left"
                        >
                            <FileText className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary shrink-0 transition-colors" />
                            <span className="text-xs text-sidebar-foreground/80 group-hover:text-foreground truncate font-medium">
                                {source.file.split('/').pop()}
                            </span>
                        </button>
                    ))}
                    {contextFiles.length === 0 && (
                        <div className="h-32 flex flex-col items-center justify-center text-center border border-dashed border-sidebar-border rounded-lg bg-sidebar-accent/10">
                             <Database className="w-6 h-6 text-muted-foreground/20 mb-2" />
                            <p className="text-[10px] text-muted-foreground max-w-[120px]">References will appear here.</p>
                        </div>
                    )}
                  </div>
              </ScrollArea>
          </div>
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border shrink-0">
           <Button 
                variant="ghost" 
                className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 h-8 px-2"
                onClick={onClear}
           >
                <Trash2 className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">Clear Session</span>
           </Button>
      </div>
    </motion.aside>
  );
}