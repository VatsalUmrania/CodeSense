import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Loader2, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThoughtChainProps {
  isVisible: boolean;
  steps?: string[];
}

export function ThoughtChain({ isVisible, steps = [] }: ThoughtChainProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [elapsed, setElapsed] = useState(0);

  const defaultSteps = [
    "Analyzing user query...",
    "Scanning codebase for context...",
    "Retrieving relevant definitions...",
    "Synthesizing answer..."
  ];

  const activeSteps = steps.length > 0 ? steps : defaultSteps;
  const currentStepIndex = Math.min(Math.floor(elapsed / 1.2), activeSteps.length - 1);

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
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mb-6 ml-12"
    >
      <div className="border border-border/40 bg-muted/10 rounded-xl overflow-hidden backdrop-blur-sm shadow-xs">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-xs font-medium text-muted-foreground hover:bg-muted/20 transition-colors"
        >
          <div className="flex items-center gap-2 text-primary/80">
            <BrainCircuit className="w-3.5 h-3.5 animate-pulse" />
            <span>Reasoning</span>
          </div>
          <span className="ml-auto font-mono text-[10px] opacity-60 bg-muted px-1.5 py-0.5 rounded">
            {elapsed.toFixed(1)}s
          </span>
          <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", isExpanded && "rotate-180")} />
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-4 pb-3 space-y-2 border-t border-border/20"
            >
              {activeSteps.map((step, idx) => {
                const isCompleted = idx < currentStepIndex;
                const isCurrent = idx === currentStepIndex;

                return (
                  <motion.div
                    key={idx}
                    initial={{ x: -5, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: idx * 0.15 }}
                    className={cn(
                      "flex items-center gap-3 text-[11px] font-mono pl-1",
                      isCurrent ? "text-foreground font-medium" : isCompleted ? "text-muted-foreground/40" : "text-muted-foreground/20"
                    )}
                  >
                    {isCurrent ? (
                      <Loader2 className="w-3 h-3 animate-spin text-primary" />
                    ) : (
                      <div className={cn("w-1.5 h-1.5 rounded-full transition-colors", isCompleted ? "bg-green-500/50" : "bg-border")} />
                    )}
                    {step}
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}