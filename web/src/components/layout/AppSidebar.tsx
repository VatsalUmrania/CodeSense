import { motion, AnimatePresence } from "framer-motion";
import { 
    Github, 
    Trash2, 
    MessageSquare, 
    Clock,
    ChevronRight
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Message } from "@/hooks/use-codesense";

interface SidebarProps {
  isOpen: boolean;
  repoUrl: string;
  ingestStatus: string;
  messages: Message[]; // Changed from contextFiles to messages
  onClear: () => void;
}

export function AppSidebar({ 
  isOpen, 
  repoUrl, 
  ingestStatus, 
  messages = [], 
  onClear 
}: SidebarProps) {
  
  const repoName = repoUrl ? repoUrl.split("github.com/")[1] : null;
  
  // Filter only user messages for the history timeline
  const history = messages.filter(m => m.role === "user");

  return (
    <motion.aside 
      initial={{ width: 280 }}
      animate={{ width: isOpen ? 280 : 0, opacity: isOpen ? 1 : 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="bg-sidebar border-r border-sidebar-border hidden md:flex flex-col shrink-0 h-full overflow-hidden text-sidebar-foreground z-30 relative shadow-2xl"
    >
      {/* --- Header --- */}
      <div className="h-16 flex items-center px-5 border-b border-sidebar-border/60 bg-sidebar/50 backdrop-blur-sm shrink-0">
         <div className="flex items-center gap-3 font-bold tracking-tight text-sm">
               <img src="/logo.svg" className="w-8 h-8" alt="Logo" />
            <span className="text-sidebar-foreground">CodeSense</span>
         </div>
      </div>
      
      {/* --- Content --- */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-8">
            
            {/* 1. Repository Section */}
            <div className="space-y-2.5">
                <h3 className="px-1 text-[10px] font-semibold text-sidebar-foreground/50 uppercase tracking-widest">
                    Target
                </h3>
                
                <div className="group relative overflow-hidden rounded-xl border border-sidebar-border bg-sidebar-accent/30 p-3 transition-all hover:bg-sidebar-accent/50 hover:border-sidebar-primary/20 hover:shadow-sm">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-background rounded-lg border border-sidebar-border text-sidebar-foreground shadow-sm shrink-0">
                            <Github className="w-4 h-4" />
                        </div>
                        <div className="flex flex-col min-w-0">
                            <span className="text-xs font-semibold truncate text-sidebar-foreground group-hover:text-primary transition-colors">
                                {repoName?.split('/')[1] || "No Repository"}
                            </span>
                            <span className="text-[10px] text-muted-foreground truncate">
                                {repoName?.split('/')[0] || "Select a repo"}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            {/* 2. Chat History Section */}
            <div className="space-y-2.5">
                <div className="flex items-center justify-between px-1">
                    <h3 className="text-[10px] font-semibold text-sidebar-foreground/50 uppercase tracking-widest">
                        History
                    </h3>
                    {history.length > 0 && (
                        <span className="text-[10px] bg-sidebar-accent px-1.5 py-0.5 rounded-md text-sidebar-foreground font-mono border border-sidebar-border/50">
                            {history.length}
                        </span>
                    )}
                </div>

                <div className="flex flex-col gap-1">
                    <AnimatePresence initial={false}>
                        {history.slice().reverse().map((msg, i) => (
                            <motion.button 
                                key={i}
                                initial={{ opacity: 0, x: -5 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="group flex items-center w-full gap-2.5 p-2.5 rounded-lg text-left hover:bg-sidebar-accent transition-all hover:shadow-sm border border-transparent hover:border-sidebar-border/50"
                            >
                                <div className="shrink-0 text-muted-foreground group-hover:text-primary transition-colors">
                                    <MessageSquare className="w-3.5 h-3.5" />
                                </div>
                                <span className="text-xs text-sidebar-foreground/80 group-hover:text-sidebar-foreground truncate flex-1 line-clamp-1">
                                    {msg.content}
                                </span>
                                <ChevronRight className="w-3 h-3 text-sidebar-foreground/20 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                            </motion.button>
                        ))}
                    </AnimatePresence>

                    {history.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-8 px-4 text-center border border-dashed border-sidebar-border/60 rounded-xl bg-sidebar-accent/5">
                            <Clock className="w-8 h-8 text-sidebar-foreground/10 mb-2" />
                            <p className="text-[10px] text-muted-foreground">
                                Your conversation history will appear here.
                            </p>
                        </div>
                    )}
                </div>
            </div>

        </div>
      </ScrollArea>
      
      {/* --- Footer --- */}
      <div className="p-4 border-t border-sidebar-border/60 bg-sidebar-accent/5 backdrop-blur-sm shrink-0">
           <Button 
                variant="outline" 
                onClick={onClear}
                className={cn(
                    "w-full justify-start h-9 px-3 text-xs font-medium text-muted-foreground hover:text-destructive hover:border-destructive/30 hover:bg-destructive/5 transition-all shadow-sm"
                )}
           >
                <Trash2 className="w-3.5 h-3.5 mr-2" />
                Clear Session
           </Button>
      </div>
    </motion.aside>
  );
}