// import { motion, AnimatePresence } from "framer-motion";
// import { 
//     Github, 
//     Trash2, 
//     MessageSquare, 
//     Clock, 
//     ChevronRight,
//     Network,
//     ShieldCheck
// } from "lucide-react";
// import { Button } from "@/components/ui/button";
// import { ScrollArea } from "@/components/ui/scroll-area";
// import { cn } from "@/lib/utils";
// import { Message } from "@/hooks/use-codesense";
// import { useRouter } from "next/navigation";

// interface SidebarProps {
//   isOpen: boolean;
//   repoUrl: string;
//   ingestStatus: string;
//   messages: Message[];
//   onClear: () => void;
// }

// const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// export function AppSidebar({ 
//   isOpen, 
//   repoUrl, 
//   ingestStatus, 
//   messages = [], 
//   onClear 
// }: SidebarProps) {
  
//   const router = useRouter();
//   const repoName = repoUrl ? repoUrl.split("github.com/")[1] : null;
  
//   // Filter only user messages for the history timeline
//   const history = messages.filter(m => m.role === "user");

//   const navigateTo = async (path: string) => {
//       if (!repoUrl) return;
      
//       // 1. Determine the Repo ID (Checking cache via ingest endpoint)
//       try {
//          // Note: We use POST because the endpoint is defined as @app.post("/ingest")
//          const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(repoUrl)}`, {
//              method: "POST" 
//          });
//          const data = await res.json();
         
//          // 2. Navigate if we have an ID
//          if (data.repo_id) {
//              router.push(`${path}?id=${data.repo_id}&url=${encodeURIComponent(repoUrl)}`);
//          } else {
//              console.error("Repository not found or not yet indexed.");
//          }
//       } catch(e) {
//           console.error("Navigation error", e);
//       }
//   };

//   return (
//     <motion.aside 
//       initial={{ width: 280 }}
//       animate={{ width: isOpen ? 280 : 0, opacity: isOpen ? 1 : 0 }}
//       transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
//       className="bg-sidebar border-r border-sidebar-border hidden md:flex flex-col shrink-0 h-full overflow-hidden text-sidebar-foreground z-30 relative shadow-2xl"
//     >
//       {/* --- Header --- */}
//       <div className="h-16 flex items-center px-5 border-b border-sidebar-border/60 bg-sidebar/50 backdrop-blur-sm shrink-0">
//          <div className="flex items-center gap-3 font-bold tracking-tight text-sm">
//                <img src="/logo.svg" className="w-8 h-8" alt="Logo" />
//             <span className="text-sidebar-foreground">CodeSense</span>
//          </div>
//       </div>
      
//       {/* --- Content --- */}
//       <ScrollArea className="flex-1">
//         <div className="p-4 space-y-8">
            
//             {/* 1. Repository Section */}
//             <div className="space-y-2.5">
//                 <h3 className="px-1 text-[10px] font-semibold text-sidebar-foreground/50 uppercase tracking-widest">
//                     Target
//                 </h3>
                
//                 <div className="group relative overflow-hidden rounded-xl border border-sidebar-border bg-sidebar-accent/30 p-3 transition-all hover:bg-sidebar-accent/50 hover:border-sidebar-primary/20 hover:shadow-sm">
//                     <div className="flex items-start gap-3">
//                         <div className="p-2 bg-background rounded-lg border border-sidebar-border text-sidebar-foreground shadow-sm shrink-0">
//                             <Github className="w-4 h-4" />
//                         </div>
//                         <div className="flex flex-col min-w-0">
//                             <span className="text-xs font-semibold truncate text-sidebar-foreground group-hover:text-primary transition-colors">
//                                 {repoName?.split('/')[1] || "No Repository"}
//                             </span>
//                             <span className="text-[10px] text-muted-foreground truncate">
//                                 {repoName?.split('/')[0] || "Select a repo"}
//                             </span>
//                         </div>
//                     </div>
//                 </div>
//             </div>

//             {/* 2. Tools Section (NEW) */}
//             <div className="space-y-2.5">
//                 <h3 className="px-1 text-[10px] font-semibold text-sidebar-foreground/50 uppercase tracking-widest">
//                     Tools
//                 </h3>
//                 <div className="grid gap-1">
//                     <Button 
//                         variant="ghost" 
//                         className="w-full justify-start h-9 px-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
//                         onClick={() => router.push(`/chat?url=${encodeURIComponent(repoUrl)}`)}
//                     >
//                         <MessageSquare className="w-4 h-4 mr-2.5 text-blue-500/80" /> 
//                         Chat
//                     </Button>
//                     <Button 
//                         variant="ghost" 
//                         className="w-full justify-start h-9 px-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
//                         onClick={() => navigateTo('/graph')}
//                     >
//                         <Network className="w-4 h-4 mr-2.5 text-purple-500/80" /> 
//                         Dependency Graph
//                     </Button>
//                     <Button 
//                         variant="ghost" 
//                         className="w-full justify-start h-9 px-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-sidebar-accent"
//                         onClick={() => navigateTo('/audit')}
//                     >
//                         <ShieldCheck className="w-4 h-4 mr-2.5 text-emerald-500/80" /> 
//                         Code Audit
//                     </Button>
//                 </div>
//             </div>

//             {/* 3. Chat History Section */}
//             <div className="space-y-2.5">
//                 <div className="flex items-center justify-between px-1">
//                     <h3 className="text-[10px] font-semibold text-sidebar-foreground/50 uppercase tracking-widest">
//                         History
//                     </h3>
//                     {history.length > 0 && (
//                         <span className="text-[10px] bg-sidebar-accent px-1.5 py-0.5 rounded-md text-sidebar-foreground font-mono border border-sidebar-border/50">
//                             {history.length}
//                         </span>
//                     )}
//                 </div>

//                 <div className="flex flex-col gap-1">
//                     <AnimatePresence initial={false}>
//                         {history.slice().reverse().map((msg, i) => (
//                             <motion.button 
//                                 key={i}
//                                 initial={{ opacity: 0, x: -5 }}
//                                 animate={{ opacity: 1, x: 0 }}
//                                 className="group flex items-center w-full gap-2.5 p-2.5 rounded-lg text-left hover:bg-sidebar-accent transition-all hover:shadow-sm border border-transparent hover:border-sidebar-border/50"
//                             >
//                                 <div className="shrink-0 text-muted-foreground group-hover:text-primary transition-colors">
//                                     <MessageSquare className="w-3.5 h-3.5" />
//                                 </div>
//                                 <span className="text-xs text-sidebar-foreground/80 group-hover:text-sidebar-foreground truncate flex-1 line-clamp-1">
//                                     {msg.content}
//                                 </span>
//                                 <ChevronRight className="w-3 h-3 text-sidebar-foreground/20 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
//                             </motion.button>
//                         ))}
//                     </AnimatePresence>

//                     {history.length === 0 && (
//                         <div className="flex flex-col items-center justify-center py-8 px-4 text-center border border-dashed border-sidebar-border/60 rounded-xl bg-sidebar-accent/5">
//                             <Clock className="w-8 h-8 text-sidebar-foreground/10 mb-2" />
//                             <p className="text-[10px] text-muted-foreground">
//                                 Your conversation history will appear here.
//                             </p>
//                         </div>
//                     )}
//                 </div>
//             </div>

//         </div>
//       </ScrollArea>
      
//       {/* --- Footer --- */}
//       <div className="p-4 border-t border-sidebar-border/60 bg-sidebar-accent/5 backdrop-blur-sm shrink-0">
//            <Button 
//                 variant="outline" 
//                 onClick={onClear}
//                 className={cn(
//                     "w-full justify-start h-9 px-3 text-xs font-medium text-muted-foreground hover:text-destructive hover:border-destructive/30 hover:bg-destructive/5 transition-all shadow-sm"
//                 )}
//            >
//                 <Trash2 className="w-3.5 h-3.5 mr-2" />
//                 Clear Session
//            </Button>
//       </div>
//     </motion.aside>
//   );
// }

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
    Github, Trash2, MessageSquare, Clock, ChevronRight, Network, ShieldCheck, FileText
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { Message } from "@/hooks/use-codesense";
import { useRouter } from "next/navigation";
import { FileTree } from "./FileTree"; // Import new component

interface SidebarProps {
  isOpen: boolean;
  repoUrl: string;
  ingestStatus: string;
  messages: Message[];
  fileStructure?: string[];
  pinnedFiles?: string[];
  onTogglePin?: (file: string) => void;
  onFileClick?: (file: string) => void;
  onClear: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AppSidebar({ 
  isOpen, 
  repoUrl, 
  ingestStatus, 
  messages = [],
  fileStructure = [],
  pinnedFiles = [],
  onTogglePin = () => {},
  onFileClick = () => {},
  onClear 
}: SidebarProps) {
  
  const router = useRouter();
  const repoName = repoUrl ? repoUrl.split("github.com/")[1] : null;
  const history = messages.filter(m => m.role === "user");

  const navigateTo = async (path: string) => {
      if (!repoUrl) return;
      try {
         const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(repoUrl)}`, { method: "POST" });
         const data = await res.json();
         if (data.repo_id) {
             router.push(`${path}?id=${data.repo_id}&url=${encodeURIComponent(repoUrl)}`);
         }
      } catch(e) { console.error(e); }
  };

  return (
    <motion.aside 
      initial={{ width: 280 }}
      animate={{ width: isOpen ? 280 : 0, opacity: isOpen ? 1 : 0 }}
      className="bg-sidebar border-r border-sidebar-border hidden md:flex flex-col shrink-0 h-full overflow-hidden text-sidebar-foreground z-30 relative shadow-2xl"
    >
      <div className="h-16 flex items-center px-5 border-b border-sidebar-border/60 bg-sidebar/50 backdrop-blur-sm shrink-0">
         <div className="flex items-center gap-3 font-bold tracking-tight text-sm">
               <img src="/logo.svg" className="w-8 h-8" alt="Logo" />
            <span className="text-sidebar-foreground">CodeSense</span>
         </div>
      </div>
      
      <div className="p-4 pb-0">
           <div className="group relative overflow-hidden rounded-xl border border-sidebar-border bg-sidebar-accent/30 p-3 mb-4 transition-all hover:bg-sidebar-accent/50 hover:border-sidebar-primary/20 hover:shadow-sm">
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

      <Tabs defaultValue="explorer" className="flex-1 flex flex-col overflow-hidden">
          <div className="px-4 mb-2">
              
                  <span>History</span>
              
          </div>

          <TabsContent value="explorer" className="flex-1 overflow-hidden mt-0">
               <ScrollArea className="h-full px-4">
                   <div className="space-y-6 pb-4">
                        {/* File Tree */}
                        <div className="space-y-2">
                             <h3 className="text-[10px] font-semibold text-sidebar-foreground/50 uppercase tracking-widest">Files</h3>
                             <FileTree 
                                files={fileStructure} 
                                pinnedFiles={pinnedFiles} 
                                onTogglePin={onTogglePin}
                                onFileClick={onFileClick}
                             />
                        </div>

                        {/* Tools */}
                        <div className="space-y-2">
                            <h3 className="text-[10px] font-semibold text-sidebar-foreground/50 uppercase tracking-widest">Tools</h3>
                            <div className="grid gap-1">
                                <Button variant="ghost" className="w-full justify-start h-8 px-2 text-xs" onClick={() => navigateTo('/chat')}>
                                    <MessageSquare className="w-3.5 h-3.5 mr-2" /> Chat
                                </Button>
                                <Button variant="ghost" className="w-full justify-start h-8 px-2 text-xs" onClick={() => navigateTo('/graph')}>
                                    <Network className="w-3.5 h-3.5 mr-2" /> Graph
                                </Button>
                                <Button variant="ghost" className="w-full justify-start h-8 px-2 text-xs" onClick={() => navigateTo('/audit')}>
                                    <ShieldCheck className="w-3.5 h-3.5 mr-2" /> Audit
                                </Button>
                            </div>
                        </div>
                   </div>
               </ScrollArea>
          </TabsContent>

          <TabsContent value="history" className="flex-1 overflow-hidden mt-0 px-4">
               <ScrollArea className="h-full">
                    <div className="space-y-1 py-2">
                        {history.slice().reverse().map((msg, i) => (
                            <div key={i} className="flex items-center gap-2 p-2 text-xs text-muted-foreground bg-sidebar-accent/30 rounded-md">
                                <MessageSquare className="w-3 h-3 shrink-0"/>
                                <span className="truncate">{msg.content}</span>
                            </div>
                        ))}
                         {history.length === 0 && (
                            <div className="text-center py-8 text-xs text-muted-foreground">No history yet.</div>
                        )}
                    </div>
               </ScrollArea>
          </TabsContent>
      </Tabs>
      
      <div className="p-4 border-t border-sidebar-border/60 bg-sidebar-accent/5 backdrop-blur-sm shrink-0">
           <Button variant="outline" onClick={onClear} className="w-full justify-start h-8 text-xs">
                <Trash2 className="w-3.5 h-3.5 mr-2" /> Clear Session
           </Button>
      </div>
    </motion.aside>
  );
}