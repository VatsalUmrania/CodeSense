import { useState } from "react";
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Github, Loader2, ArrowRight, GitBranch, Search } from "lucide-react";
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

    const owner = currentRepoUrl ? currentRepoUrl.split("github.com/")[1]?.split("/")[0] : null;
    const repo = currentRepoUrl ? currentRepoUrl.split("github.com/")[1]?.split("/")[1] : null;

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <button className="group flex items-center gap-2 pl-1 pr-3 py-1 rounded-full bg-background border border-border/60 hover:border-primary/30 hover:shadow-md transition-all duration-300 max-w-[300px]">
                    <div className="w-7 h-7 rounded-full bg-muted/50 flex items-center justify-center border border-border group-hover:bg-primary/5 transition-colors">
                        <Github className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary" />
                    </div>

                    <div className="flex flex-col items-start min-w-0">
                        {repo ? (
                            <div className="flex items-center gap-1 text-xs">
                                <span className="text-muted-foreground/80">{owner}</span>
                                <span className="text-muted-foreground/40">/</span>
                                <span className="font-medium text-foreground">{repo}</span>
                            </div>
                        ) : (
                            <span className="text-xs font-medium text-muted-foreground">Select Repository</span>
                        )}
                    </div>

                    <div className="ml-auto pl-2">
                        <GitBranch className="w-3 h-3 text-muted-foreground/50 group-hover:text-primary/50" />
                    </div>
                </button>
            </DialogTrigger>

            <DialogContent className="sm:max-w-[480px] gap-0 p-0 overflow-hidden bg-background/95 backdrop-blur-xl border-border shadow-2xl rounded-2xl">
                <div className="p-6 pb-2">
                    <DialogTitle className="text-xl font-semibold tracking-tight">Sync Codebase</DialogTitle>
                    <p className="text-sm text-muted-foreground mt-1.5">
                        Enter a GitHub URL to index the repository for context-aware chat.
                    </p>
                </div>

                <div className="p-6 pt-4 space-y-4">
                    <div className="relative group">
                        <div className="absolute left-3 top-3 bg-muted/50 p-0.5 rounded">
                            <Github className="h-3.5 w-3.5 text-muted-foreground" />
                        </div>
                        <Input
                            placeholder="github.com/owner/repo"
                            className="pl-10 h-11 bg-muted/20 border-border/60 focus-visible:ring-1 focus-visible:ring-primary/20 focus-visible:border-primary/30 transition-all font-mono text-sm"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                        <Button variant="ghost" onClick={() => setOpen(false)} className="text-muted-foreground hover:text-foreground">Cancel</Button>
                        <Button onClick={handleSubmit} disabled={isIngesting || !url} className="min-w-[120px] shadow-lg shadow-primary/10">
                            {isIngesting ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Indexing...
                                </>
                            ) : (
                                <>
                                    <span>Start Sync</span>
                                    <ArrowRight className="w-4 h-4 ml-2 opacity-50" />
                                </>
                            )}
                        </Button>
                    </div>
                </div>

                <div className="px-6 py-4 bg-muted/10 border-t border-border/40 text-[11px] text-muted-foreground/70 flex justify-between items-center">
                    <span className="flex items-center gap-1.5">
                        <Search className="w-3 h-3" />
                        Supports public repositories
                    </span>
                    <span className="font-mono opacity-50">ESC to close</span>
                </div>
            </DialogContent>
        </Dialog>
    );
}