import { motion } from "framer-motion";
import {
    MessageSquare,
    Network,
    ShieldCheck,
    Plus,
    PanelLeftClose,
    PanelLeftOpen,
    MoreHorizontal,
    Trash2,
    Command,
    LogOut
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { ChatSession } from "@/hooks/use-codesense";
import { useRouter } from "next/navigation";
import { Separator } from "@/components/ui/separator";

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

    const NavItem = ({ icon: Icon, label, path, active = false }: any) => (
        <button
            onClick={() => navigateTo(path)}
            className={cn(
                "flex items-center gap-3 p-2 rounded-lg transition-all duration-200 group relative",
                active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground",
                isCollapsed ? "justify-center" : "w-full"
            )}
            title={label}
        >
            <Icon className={cn("w-4 h-4 shrink-0 transition-colors", active ? "text-primary" : "group-hover:text-primary")} />
            {!isCollapsed && (
                <span className="text-sm font-medium">{label}</span>
            )}
            {isCollapsed && active && (
                <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-primary rounded-r-full" />
            )}
        </button>
    );

    return (
        <motion.aside
            initial={false}
            animate={{ width: isCollapsed ? 70 : 260 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }} // Bezier for smooth "snap"
            className="h-full bg-sidebar/50 backdrop-blur-xl border-r border-sidebar-border flex flex-col overflow-hidden z-30 relative"
        >
            {/* --- Header --- */}
            <div className="p-4 flex items-center justify-between shrink-0 h-16">
                {!isCollapsed && (
                    <div className="flex items-center gap-2 font-semibold text-foreground tracking-tight animate-in fade-in duration-300">
                        <div className="w-6 h-6 bg-primary rounded-md flex items-center justify-center">
                            <Command className="w-3.5 h-3.5 text-primary-foreground" />
                        </div>
                        <span>CodeSense</span>
                    </div>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleSidebar}
                    className={cn("text-muted-foreground hover:text-foreground", isCollapsed && "mx-auto")}
                >
                    {isCollapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
                </Button>
            </div>

            {/* --- Main Actions --- */}
            <div className="px-3 py-2 space-y-1">
                <Button
                    onClick={onClear}
                    className={cn(
                        "w-full shadow-sm transition-all",
                        isCollapsed ? "h-10 w-10 p-0 rounded-xl" : "justify-start px-3"
                    )}
                >
                    <Plus className={cn("w-4 h-4", !isCollapsed && "mr-2")} />
                    {!isCollapsed && "New Chat"}
                </Button>
            </div>

            <Separator className="my-2 mx-4 w-auto opacity-50" />

            {/* --- Navigation --- */}
            <div className="px-3 space-y-1">
                <NavItem icon={MessageSquare} label="Chat" path="/chat" active={true} />
                <NavItem icon={Network} label="Graph" path="/graph" />
                <NavItem icon={ShieldCheck} label="Audit" path="/audit" />
            </div>

            {/* --- History --- */}
            <div className="flex-1 min-h-0 flex flex-col mt-6">
                {!isCollapsed && (
                    <div className="px-4 pb-2 text-[10px] font-semibold text-muted-foreground/60 uppercase tracking-wider">
                        Recent Activity
                    </div>
                )}

                <ScrollArea className="flex-1">
                    <div className={cn("space-y-1 px-3 pb-4", isCollapsed && "flex flex-col items-center")}>
                        {validSessions.map((session) => (
                            isCollapsed ? (
                                // Collapsed Dot Indicator
                                <div
                                    key={session.id}
                                    onClick={() => onSessionSelect(session.id)}
                                    className={cn(
                                        "w-2 h-2 rounded-full cursor-pointer hover:scale-125 transition-all my-1.5",
                                        currentSessionId === session.id ? "bg-primary" : "bg-border hover:bg-muted-foreground"
                                    )}
                                    title={session.title}
                                />
                            ) : (
                                // Expanded Item
                                <div
                                    key={session.id}
                                    className={cn(
                                        "group flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all hover:bg-sidebar-accent/50 text-muted-foreground hover:text-foreground",
                                        currentSessionId === session.id && "bg-sidebar-accent text-foreground shadow-sm"
                                    )}
                                    onClick={() => onSessionSelect(session.id)}
                                >
                                    <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
                                    <span className="text-xs truncate flex-1 leading-none">
                                        {session.title || "Untitled Conversation"}
                                    </span>

                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <div role="button" className="opacity-0 group-hover:opacity-100 p-1 hover:bg-background/80 rounded transition-opacity">
                                                <MoreHorizontal className="w-3 h-3" />
                                            </div>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end" className="w-40">
                                            <DropdownMenuItem onClick={(e) => { e.stopPropagation(); onSessionDelete(session.id); }} className="text-destructive focus:text-destructive cursor-pointer text-xs">
                                                <Trash2 className="w-3.5 h-3.5 mr-2" /> Delete Chat
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            )
                        ))}
                    </div>
                </ScrollArea>
            </div>

            {/* --- User/Footer --- */}
            <div className="p-3 border-t border-sidebar-border mt-auto">
                {!isCollapsed ? (
                    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-sidebar-accent/50 transition-colors cursor-pointer">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white font-medium text-xs shadow-md">
                            CS
                        </div>
                        <div className="flex flex-col min-w-0">
                            <span className="text-xs font-medium truncate">User Account</span>
                            <span className="text-[10px] text-muted-foreground truncate">Free Plan</span>
                        </div>
                    </div>
                ) : (
                    <div className="flex justify-center">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 shadow-md" />
                    </div>
                )}
            </div>

        </motion.aside>
    );
}