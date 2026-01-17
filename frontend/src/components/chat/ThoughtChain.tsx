import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ChevronDown, ChevronRight, Loader2, FileSearch, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThoughtChainProps {
  isVisible: boolean;
  steps?: string[]; // Optional: if your backend streams specific steps
}

export function ThoughtChain({ isVisible, steps = [] }: ThoughtChainProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [elapsed, setElapsed] = useState(0);

  // Fake "steps" for visual feedback if none provided
  const defaultSteps = [
    "Analyzing context...",
    "Retrieving relevant files...",
    "Ranking citations...",
    "Synthesizing response..."
  ];

  const activeSteps = steps.length > 0 ? steps : defaultSteps;
  const currentStepIndex = Math.min(Math.floor(elapsed / 0.8), activeSteps.length - 1);

  useEffect(() => {
    if (!isVisible) {
      setElapsed(0);
      return;
    }
    const interval = setInterval(() => setElapsed((prev) => prev + 0.1), 100);
    return () => clearInterval(interval);
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div className="w-full max-w-3xl mb-6">
      <div className="border border-border/50 bg-muted/20 rounded-lg overflow-hidden backdrop-blur-sm">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center gap-3 px-4 py-3 text-xs font-medium text-muted-foreground hover:bg-muted/30 transition-colors"
        >
          <div className="flex items-center gap-2 text-primary">
            <BrainCircuit className="w-4 h-4 animate-pulse" />
            <span>Reasoning...</span>
          </div>
          <span className="ml-auto font-mono text-[10px] opacity-70">
            {elapsed.toFixed(1)}s
          </span>
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-4 pb-3 space-y-2 border-t border-border/30 bg-muted/10"
            >
              {activeSteps.map((step, idx) => {
                const isCompleted = idx < currentStepIndex;
                const isCurrent = idx === currentStepIndex;

                return (
                  <motion.div
                    key={idx}
                    initial={{ x: -10, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: idx * 0.1 }}
                    className={cn(
                      "flex items-center gap-3 text-[11px] font-mono",
                      isCurrent ? "text-foreground" : isCompleted ? "text-muted-foreground/50 line-through" : "text-muted-foreground/30"
                    )}
                  >
                    {isCurrent ? (
                      <Loader2 className="w-3 h-3 animate-spin text-primary" />
                    ) : (
                      <div className={cn("w-3 h-3 rounded-full border border-current flex items-center justify-center", isCompleted && "border-primary/50")}>
                        {isCompleted && <div className="w-1.5 h-1.5 bg-primary/50 rounded-full" />}
                      </div>
                    )}
                    {step}
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}