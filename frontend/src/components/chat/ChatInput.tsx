import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, ArrowUp } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface ChatInputProps {
  onSend: (msg: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "inherit";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "inherit";
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <motion.div
      layout
      className="relative group"
    >
      {/* Glow Effect */}
      <div className={cn(
        "absolute -inset-0.5 bg-linear-to-r from-primary/20 via-blue-500/20 to-primary/20 rounded-[28px] opacity-0 transition-opacity duration-500 blur-md",
        isFocused && "opacity-100"
      )} />

      <div className={cn(
        "relative flex items-end gap-2 bg-background/80 backdrop-blur-xl border rounded-[24px] shadow-2xl transition-all duration-300 overflow-hidden pl-4 pr-3 py-3",
        isFocused ? "border-primary/40 ring-1 ring-primary/10" : "border-border/60"
      )}>
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything..."
          className="flex-1 min-h-[24px] max-h-[200px] border-none shadow-none focus-visible:ring-0 resize-none bg-transparent text-[15px] leading-relaxed py-1 px-0 placeholder:text-muted-foreground/40"
          disabled={disabled}
          rows={1}
        />

        <Button
          onClick={handleSend}
          size="icon"
          className={cn(
            "h-8 w-8 rounded-full transition-all duration-300 shrink-0 mb-0.5",
            input.trim()
              ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md scale-100"
              : "bg-muted text-muted-foreground cursor-not-allowed scale-90 opacity-0"
          )}
          disabled={disabled || !input.trim()}
        >
          <ArrowUp className="w-4 h-4 stroke-[3px]" />
        </Button>
      </div>

      <div className="mt-3 text-center opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-700">
        <p className="text-[10px] text-muted-foreground/40 font-medium">
          AI can make mistakes. Check important info.
        </p>
      </div>
    </motion.div>
  );
}