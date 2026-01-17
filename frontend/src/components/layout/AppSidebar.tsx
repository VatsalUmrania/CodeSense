// import { useState } from "react";
// import { motion } from "framer-motion";
// import {
//     Github, Trash2, MessageSquare, Clock, Network, ShieldCheck, Plus, 
//     MoreHorizontal, FolderTree, LayoutGrid
// } from "lucide-react";
// import { Button } from "@/components/ui/button";
// import { ScrollArea } from "@/components/ui/scroll-area";
// import { Separator } from "@/components/ui/separator";
// import {
//     DropdownMenu,
//     DropdownMenuContent,
//     DropdownMenuItem,
//     DropdownMenuTrigger,
// } from "@/components/ui/dropdown-menu";
// import { cn } from "@/lib/utils";
// import { ChatSession } from "@/hooks/use-codesense";
// import { useRouter } from "next/navigation";
// import { FileTree } from "./FileTree";

// interface SidebarProps {
//   isOpen: boolean;
//   repoUrl: string;
//   ingestStatus: string;
//   // messages is kept for prop compatibility but not used in this modern layout
//   messages?: any[]; 
//   fileStructure?: string[];
//   pinnedFiles?: string[];
//   sessions?: ChatSession[];
//   currentSessionId?: string | null;
//   onTogglePin?: (file: string) => void;
//   onFileClick?: (file: string) => void;
//   onSessionSelect?: (id: string) => void;
//   onSessionDelete?: (id: string) => void;
//   onClear: () => void;
// }

// const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// export function AppSidebar({
//   isOpen,
//   repoUrl,
//   fileStructure = [],
//   pinnedFiles = [],
//   sessions = [],
//   currentSessionId,
//   onTogglePin = () => {},
//   onFileClick = () => {},
//   onSessionSelect = () => {},
//   onSessionDelete = () => {},
//   onClear
// }: SidebarProps) {

//   const router = useRouter();
//   const repoName = repoUrl ? repoUrl.split("github.com/")[1] : "Select Repository";
//   const [activeTab, setActiveTab] = useState<"files" | "history">("files");

//   // Filter: Ensure we don't show null/undefined sessions or sessions without IDs
//   const validSessions = sessions.filter(s => s && s.id);

//   const navigateTo = async (path: string) => {
//       if (!repoUrl) return;
//       try {
//          const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(repoUrl)}`, { method: "POST" });
//          const data = await res.json();
//          if (data.repo_id) {
//              router.push(`${path}?id=${data.repo_id}&url=${encodeURIComponent(repoUrl)}`);
//          }
//       } catch(e) { console.error(e); }
//   };

//   return (
//     <motion.aside
//       initial={{ width: 280, opacity: 0 }}
//       animate={{ width: isOpen ? 280 : 0, opacity: isOpen ? 1 : 0 }}
//       transition={{ duration: 0.3, ease: "easeInOut" }}
//       className="h-full bg-sidebar border-r border-sidebar-border flex flex-col overflow-hidden shadow-xl z-30"
//     >
//       {/* --- Header: Brand --- */}
//       <div className="h-14 flex items-center px-4 border-b border-sidebar-border/60 bg-sidebar-accent/10 shrink-0">
//          <div className="flex items-center gap-2 font-bold text-foreground tracking-tight cursor-pointer" onClick={() => router.push('/')}>
//             <div className="w-7 h-7 bg-primary/10 rounded-lg flex items-center justify-center border border-primary/20">
//                 <img src="/logo.svg" className="w-4 h-4" alt="Logo" />
//             </div>
//             <span className="text-sm">CodeSense</span>
//          </div>
//       </div>

//       {/* --- Repo Info Card --- */}
//       <div className="p-4 pb-2 shrink-0">
//         <div className="bg-sidebar-accent/40 border border-sidebar-border rounded-xl p-3 flex items-start gap-3 shadow-sm group transition-all hover:border-primary/30 hover:bg-sidebar-accent/60">
//             <div className="p-2 bg-background rounded-lg border border-sidebar-border shrink-0 text-muted-foreground group-hover:text-foreground transition-colors">
//                 <Github className="w-4 h-4" />
//             </div>
//             <div className="flex flex-col min-w-0 overflow-hidden">
//                 <span className="text-xs font-semibold text-foreground truncate">
//                     {repoName.split('/')[1] || "No Repo"}
//                 </span>
//                 <span className="text-[10px] text-muted-foreground truncate">
//                     {repoName.split('/')[0] || "Owner"}
//                 </span>
//             </div>
//         </div>
//       </div>

//       {/* --- Navigation --- */}
//       <div className="px-4 py-2 grid gap-1 shrink-0">
//           <Button 
//             variant="ghost" 
//             size="sm" 
//             className="justify-start text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 h-8 px-2 font-medium" 
//             onClick={() => navigateTo('/chat')}
//           >
//              <MessageSquare className="w-4 h-4 mr-2 text-blue-500" /> Chat
//           </Button>
//           <Button 
//             variant="ghost" 
//             size="sm" 
//             className="justify-start text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 h-8 px-2 font-medium" 
//             onClick={() => navigateTo('/graph')}
//           >
//              <Network className="w-4 h-4 mr-2 text-purple-500" /> Graph
//           </Button>
//           <Button 
//             variant="ghost" 
//             size="sm" 
//             className="justify-start text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 h-8 px-2 font-medium" 
//             onClick={() => navigateTo('/audit')}
//           >
//              <ShieldCheck className="w-4 h-4 mr-2 text-emerald-500" /> Audit
//           </Button>
//       </div>

//       <Separator className="my-2 opacity-50" />

//       {/* --- Tabs for Files / History --- */}
//       <div className="px-4 flex gap-6 mb-2 shrink-0 border-b border-sidebar-border/40">
//           <button
//             onClick={() => setActiveTab("files")}
//             className={cn(
//                 "text-xs font-medium pb-2 border-b-2 transition-all relative top-px",
//                 activeTab === "files" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
//             )}
//           >
//             Explorer
//           </button>
//           <button
//             onClick={() => setActiveTab("history")}
//             className={cn(
//                 "text-xs font-medium pb-2 border-b-2 transition-all relative top-px",
//                 activeTab === "history" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
//             )}
//           >
//             Chats
//           </button>
//       </div>

//       {/* --- Scrollable Content --- */}
//       <ScrollArea className="flex-1 px-4 pt-2">
//         {activeTab === "files" ? (
//             <div className="pb-4">
//                  <FileTree
//                     files={fileStructure}
//                     pinnedFiles={pinnedFiles}
//                     onTogglePin={onTogglePin}
//                     onFileClick={onFileClick}
//                  />
//                  {fileStructure.length === 0 && (
//                     <div className="text-center py-10 text-xs text-muted-foreground flex flex-col items-center">
//                         <FolderTree className="w-8 h-8 mb-2 opacity-20" />
//                         <span>No files indexed.</span>
//                     </div>
//                  )}
//             </div>
//         ) : (
//             <div className="pb-4 space-y-1">
//                  <Button
//                     variant="outline"
//                     className="w-full justify-start h-8 text-xs mb-3 border-dashed border-sidebar-border/80 hover:bg-sidebar-accent text-muted-foreground hover:text-foreground"
//                     onClick={onClear}
//                 >
//                     <Plus className="w-3.5 h-3.5 mr-2" /> New Chat
//                 </Button>

//                 {validSessions.map((session) => (
//                     <div
//                         key={session.id}
//                         className={cn(
//                             "group flex items-center justify-between p-2 rounded-lg text-xs cursor-pointer transition-all border border-transparent",
//                             currentSessionId === session.id
//                                 ? "bg-sidebar-accent text-foreground border-sidebar-border/50 shadow-sm"
//                                 : "text-muted-foreground hover:bg-sidebar-accent/40 hover:text-foreground"
//                         )}
//                         onClick={() => onSessionSelect(session.id)}
//                     >
//                         <div className="flex items-center gap-2 overflow-hidden">
//                             <MessageSquare className={cn("w-3.5 h-3.5 shrink-0", currentSessionId === session.id ? "text-primary" : "opacity-70")} />
//                             <span className="truncate">{session.title || "Untitled Chat"}</span>
//                         </div>

//                         <DropdownMenu>
//                             <DropdownMenuTrigger asChild>
//                                 <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-background/80 rounded-md focus:opacity-100 outline-none transition-opacity">
//                                     <MoreHorizontal className="w-3 h-3" />
//                                 </button>
//                             </DropdownMenuTrigger>
//                             <DropdownMenuContent align="end" className="w-32">
//                                 <DropdownMenuItem onClick={(e : any) => { e.stopPropagation(); onSessionDelete(session.id); }} className="text-destructive text-xs focus:text-destructive cursor-pointer">
//                                     <Trash2 className="w-3 h-3 mr-2" /> Delete
//                                 </DropdownMenuItem>
//                             </DropdownMenuContent>
//                         </DropdownMenu>
//                     </div>
//                 ))}

//                 {validSessions.length === 0 && (
//                     <div className="text-center py-10 text-xs text-muted-foreground flex flex-col items-center">
//                         <Clock className="w-8 h-8 mb-2 opacity-20" />
//                         <span>No recent chats.</span>
//                     </div>
//                 )}
//             </div>
//         )}
//       </ScrollArea>

//     </motion.aside>
//   );
// }


import { useState } from "react";
import { motion } from "framer-motion";
import {
    MessageSquare,
    Network,
    ShieldCheck,
    Plus,
    PanelLeft,
    MoreHorizontal,
    Trash2,
    Clock, // Added Clock icon
    History
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { ChatSession } from "@/hooks/use-codesense";
import { useRouter } from "next/navigation";

interface SidebarProps {
    isCollapsed: boolean;
    toggleSidebar: () => void;
    repoUrl: string;
    sessions?: ChatSession[];
    currentSessionId?: string | null;
    onSessionSelect?: (id: string) => void;
    onSessionDelete?: (id: string) => void;
    onClear: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export function AppSidebar({
    isCollapsed,
    toggleSidebar,
    repoUrl,
    sessions = [],
    currentSessionId,
    onSessionSelect = () => { },
    onSessionDelete = () => { },
    onClear
}: SidebarProps) {

    const router = useRouter();
    // Filter out empty or invalid sessions just in case
    const validSessions = sessions.filter(s => s && s.id);

    const navigateTo = async (path: string) => {
        if (!repoUrl) return;
        try {
            const res = await fetch(`${API_URL}/ingest?url=${encodeURIComponent(repoUrl)}`, { method: "POST" });
            const data = await res.json();
            if (data.repo_id) {
                router.push(`${path}?id=${data.repo_id}&url=${encodeURIComponent(repoUrl)}`);
            }
        } catch (e) { console.error(e); }
    };

    return (
        <motion.aside
            initial={{ width: 280 }}
            animate={{ width: isCollapsed ? 60 : 280 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="h-full bg-muted/5 border-r border-border flex flex-col overflow-hidden shadow-sm z-30 relative group"
        >
            {/* --- Header --- */}
            <div className="p-3 flex flex-col gap-4 shrink-0">
                <div className={cn("flex items-center", isCollapsed ? "justify-center" : "justify-between px-1")}>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={toggleSidebar}
                        className="text-muted-foreground hover:text-foreground h-8 w-8"
                        title={isCollapsed ? "Expand" : "Collapse"}
                    >
                        <PanelLeft className="w-5 h-5" />
                    </Button>
                </div>

                <Button
                    onClick={onClear}
                    variant="secondary"
                    className={cn(
                        "rounded-full transition-all shadow-sm hover:shadow-md bg-sidebar-accent border border-sidebar-border/50",
                        isCollapsed ? "h-10 w-10 p-0 justify-center" : "h-10 justify-start px-4 gap-3"
                    )}
                    title="New Chat"
                >
                    <Plus className="w-5 h-5 text-primary" />
                    {!isCollapsed && <span className="text-sm font-medium text-foreground">New Chat</span>}
                </Button>
            </div>

            {/* --- Navigation Tools --- */}
            <div className={cn("py-2", isCollapsed ? "flex flex-col items-center gap-2" : "px-4 space-y-1")}>
                {isCollapsed ? (
                    <>
                        <Button variant="ghost" size="icon" onClick={() => navigateTo('/chat')} title="Chat"><MessageSquare className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="icon" onClick={() => navigateTo('/graph')} title="Graph"><Network className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="icon" onClick={() => navigateTo('/audit')} title="Audit"><ShieldCheck className="w-4 h-4" /></Button>
                        {/* Collapsed History Icon - acts as toggle or jump to recent */}
                        <Button variant="ghost" size="icon" onClick={toggleSidebar} title="History"><History className="w-4 h-4 text-muted-foreground" /></Button>
                    </>
                ) : (
                    <>
                        <p className="text-[10px] font-medium text-muted-foreground mb-2 uppercase tracking-wider">Tools</p>
                        <Button variant="ghost" size="sm" onClick={() => navigateTo('/chat')} className="w-full justify-start h-8 px-2 text-muted-foreground hover:text-primary">
                            <MessageSquare className="w-4 h-4 mr-2" /> Chat
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => navigateTo('/graph')} className="w-full justify-start h-8 px-2 text-muted-foreground hover:text-primary">
                            <Network className="w-4 h-4 mr-2" /> Graph
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => navigateTo('/audit')} className="w-full justify-start h-8 px-2 text-muted-foreground hover:text-primary">
                            <ShieldCheck className="w-4 h-4 mr-2" /> Audit
                        </Button>
                    </>
                )}
            </div>

            {/* --- Recent Chats (Visible Only When Expanded) --- */}
            {!isCollapsed && (
                <div className="flex-1 min-h-0 flex flex-col pt-4 animate-in fade-in slide-in-from-left-2 duration-300">
                    <div className="px-4 text-[10px] font-medium text-muted-foreground mb-1 uppercase tracking-wider shrink-0">Recent</div>

                    <div className="flex-1 min-h-0 px-2">
                        <ScrollArea className="h-full">
                            <div className="space-y-1 pb-2 pr-2">
                                {validSessions.map((session) => (
                                    <div
                                        key={session.id}
                                        className={cn(
                                            "group flex items-center gap-2 p-2 rounded-full cursor-pointer transition-colors relative hover:bg-sidebar-accent/50",
                                            currentSessionId === session.id && "bg-sidebar-accent/70 font-medium text-primary"
                                        )}
                                        onClick={() => onSessionSelect(session.id)}
                                        title={session.title || "Chat"}
                                    >
                                        <MessageSquare className={cn("w-4 h-4 shrink-0", currentSessionId === session.id ? "text-primary" : "text-muted-foreground")} />

                                        <span className="text-xs truncate flex-1 text-foreground/90">
                                            {session.title || "Untitled Chat"}
                                        </span>

                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-background rounded-full focus:opacity-100 outline-none transition-opacity absolute right-2">
                                                    <MoreHorizontal className="w-3 h-3 text-muted-foreground" />
                                                </button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onSessionDelete(session.id); }} className="text-destructive text-xs cursor-pointer">
                                                    <Trash2 className="w-3 h-3 mr-2" /> Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                ))}

                                {validSessions.length === 0 && (
                                    <div className="text-center py-6 text-xs text-muted-foreground/50 italic">
                                        No history yet.
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                    </div>
                </div>
            )}

            {/* --- Footer --- */}
            {!isCollapsed && (
                <div className="p-4 border-t border-border/40 shrink-0">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        <span>CodeSense v1.0</span>
                    </div>
                </div>
            )}
        </motion.aside>
    );
}