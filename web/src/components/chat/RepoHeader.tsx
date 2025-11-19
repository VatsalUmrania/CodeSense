import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Search } from "lucide-react";
import { useState } from "react";

interface RepoHeaderProps {
  onIngest: (url: string) => void;
  status: string;
}

export function RepoHeader({ onIngest, status }: RepoHeaderProps) {
  const [url, setUrl] = useState("");
  const isLoading = status === "loading";

  return (
    <header className="h-16 border-b border-border flex items-center justify-center px-6 bg-background/80 backdrop-blur-md sticky top-0 z-20 shrink-0">
      <div className="flex items-center gap-2 w-full max-w-xl ml-8">
         <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input 
                placeholder="Paste GitHub URL (e.g. https://github.com/owner/repo)..." 
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="pl-9 h-9 bg-muted/30 border-border focus:bg-background text-sm"
                disabled={isLoading}
            />
         </div>
         <Button 
            onClick={() => onIngest(url)} 
            disabled={isLoading} 
            size="sm" 
            className="h-9 px-4"
         >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin"/> : "Import"}
         </Button>
      </div>
    </header>
  );
}