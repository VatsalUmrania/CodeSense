import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";
import { useState } from "react";

interface ChatInputProps {
  onSend: (msg: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  return (
    <div className="p-4 border-t border-border bg-background shrink-0">
      <div className="max-w-3xl mx-auto relative">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the code..."
          className="pr-12 py-6 shadow-sm border-border bg-muted/20 focus:bg-background text-base rounded-xl"
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={disabled}
        />
        <Button 
          onClick={handleSend} 
          size="icon"
          className="absolute right-2 top-1/2 -translate-y-1/2 h-9 w-9 rounded-lg"
          disabled={disabled || !input.trim()}
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}