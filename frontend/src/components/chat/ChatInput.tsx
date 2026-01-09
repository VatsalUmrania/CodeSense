import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Paperclip, Sparkles } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (msg: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  return (
    <div className="absolute bottom-0 left-0 right-0 p-6 pb-8 bg-linear-to-t from-background via-background/90 to-transparent z-20">
      <div className={cn(
          "max-w-7xl mx-auto relative transition-all duration-300 ease-out",
          isFocused ? "scale-[1.01] -translate-y-1" : "scale-100"
      )}>
        
        {/* Input Container */}
        <div className={cn(
            "relative flex items-center gap-2 bg-background border rounded-2xl shadow-lg transition-all duration-300 overflow-hidden pl-4 pr-2 py-2",
            isFocused ? "border-primary/50 shadow-primary/5 ring-1 ring-primary/10" : "border-border shadow-black/5"
        )}>
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Ask a question about your code..."
              className="flex-1 border-none shadow-none focus-visible:ring-0 bg-transparent text-base h-10 px-2 placeholder:text-muted-foreground/50"
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={disabled}
              autoComplete="off"
            />

            <Button 
              onClick={handleSend} 
              size="icon"
              className={cn(
                  "h-9 w-9 rounded-xl transition-all duration-300 shrink-0",
                  input.trim() ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md" : "bg-muted text-muted-foreground cursor-not-allowed"
              )}
              disabled={disabled || !input.trim()}
            >
            <Send className="w-4 h-4 fill-current" /> 
            </Button>
        </div>
        
        {/* Footer Tip */}
        <div className="mt-2 text-center">
             <p className="text-[10px] text-muted-foreground/50 font-medium">
                CodeSense can make mistakes. Please verify important information.
             </p>
        </div>

      </div>
    </div>
  );
}