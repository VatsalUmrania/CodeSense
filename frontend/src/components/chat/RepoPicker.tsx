import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Github, Plus, RefreshCw, Loader2, Search } from "lucide-react";
import { cn } from "@/lib/utils";

interface RepoPickerProps {
    currentRepoUrl: string | null;
    onIngest: (url: string) => void;
    isIngesting: boolean;
}

export function RepoPicker({ currentRepoUrl, onIngest, isIngesting }: RepoPickerProps) {
    const [open, setOpen] = useState(false);
    const [url, setUrl] = useState("");

    const handleSubmit = () => {
        if (!url) return;
        onIngest(url);
        setOpen(false);
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border/60 bg-muted/20 hover:bg-muted/40 transition-colors cursor-pointer group">
                     <Github className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground" />
                     <span className="text-xs font-medium text-foreground/80 max-w-[150px] truncate">
                        {currentRepoUrl ? currentRepoUrl.replace("https://github.com/", "") : "Select Repository"}
                     </span>
                     <div className="w-px h-3 bg-border mx-1" />
                     <span className="text-[10px] text-muted-foreground group-hover:text-primary">Switch</span>
                </div>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md gap-0 p-0 overflow-hidden bg-background border-border shadow-2xl">
                <div className="p-6 pb-4 border-b border-border/40 bg-muted/10">
                    <DialogTitle className="text-lg font-medium tracking-tight mb-2">Sync Repository</DialogTitle>
                    <p className="text-sm text-muted-foreground">
                        Paste a GitHub URL to index the codebase for semantic search.
                    </p>
                </div>
                
                <div className="p-6 space-y-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input 
                            placeholder="https://github.com/owner/repo" 
                            className="pl-9 h-10 bg-muted/20 border-border/50 focus-visible:ring-1 focus-visible:ring-primary/20"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                        />
                    </div>
                    
                    <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>Cancel</Button>
                        <Button size="sm" onClick={handleSubmit} disabled={isIngesting || !url}>
                            {isIngesting && <Loader2 className="w-3 h-3 mr-2 animate-spin" />}
                            {isIngesting ? "Syncing..." : "Sync Repository"}
                        </Button>
                    </div>
                </div>

                {/* Optional: Show recent repos logic would go here */}
                <div className="px-6 py-3 bg-muted/20 border-t border-border/40 text-[10px] text-muted-foreground flex items-center gap-2">
                    <RefreshCw className="w-3 h-3" />
                    <span>Syncs usually take 1-2 minutes depending on size.</span>
                </div>
            </DialogContent>
        </Dialog>
    );
}