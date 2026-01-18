"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Bot, GitBranch, ShieldCheck, Zap, Terminal, Cpu, Search, ChevronDown, Github, CheckCircle2, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";

// --- ANIMATION VARIANTS ---
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

export default function LandingPage() {
  // FAQ State
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenFaq(openFaq === index ? null : index);
  };

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-primary/20 selection:text-primary overflow-x-hidden font-sans">

      {/* --- BRANDING HEADER --- */}
      {/* Aligns with the Clerk buttons in Layout.tsx */}
      <div className="absolute top-0 left-0 p-4 md:p-6 z-40 flex items-center gap-3">
        <div className="relative w-8 h-8 md:w-10 md:h-10">
          <Image
            src="/logo.svg"
            alt="CodeSense Logo"
            fill
            className="object-contain"
            priority
          />
        </div>
        <span className="font-bold text-lg md:text-xl tracking-tight hidden sm:block">CodeSense</span>
      </div>

      <main className="pt-32 pb-20">

        {/* --- HERO SECTION --- */}
        <section className="max-w-7xl mx-auto px-6 text-center relative z-10">

          {/* Ambient Background Glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[300px] md:w-[600px] h-[300px] md:h-[600px] bg-primary/20 rounded-full blur-[120px] -z-10 pointer-events-none" />

          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="space-y-8 max-w-4xl mx-auto"
          >
            {/* Version Badge */}
            <motion.div variants={fadeInUp} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-border bg-muted/50 backdrop-blur-sm text-sm font-medium text-muted-foreground mb-4 hover:bg-muted/80 transition-colors cursor-default">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              v1.0 Public Beta
            </motion.div>

            {/* Main Headline */}
            <motion.h1
              variants={fadeInUp}
              className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1]"
            >
              Talk to your codebase. <br />
              <span className="text-primary relative whitespace-nowrap">
                Understand it instantly.
                {/* Underline decoration */}
                <svg className="absolute -bottom-2 left-0 w-full h-3 text-primary/30" viewBox="0 0 100 10" preserveAspectRatio="none">
                  <path d="M0 5 Q 50 10 100 5" stroke="currentColor" strokeWidth="2" fill="none" />
                </svg>
              </span>
            </motion.h1>

            {/* Subtext */}
            <motion.p
              variants={fadeInUp}
              className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            >
              Stop searching through generic docs. CodeSense ingests your GitHub repos and lets you chat, visualize dependencies, and audit security in real-time.
            </motion.p>

            {/* CTAs */}
            <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
              <Link href="/chat">
                <Button size="lg" className="h-12 px-8 rounded-full text-base font-semibold shadow-lg shadow-primary/20 hover:scale-105 transition-transform w-full sm:w-auto">
                  Start Analyzing <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </Link>
              <Link href="https://github.com/vatsalumrania/codesense" target="_blank">
                <Button size="lg" variant="outline" className="h-12 px-8 rounded-full text-base bg-background/50 backdrop-blur border-border hover:bg-muted w-full sm:w-auto">
                  <Github className="mr-2 w-4 h-4" /> Star on GitHub
                </Button>
              </Link>
            </motion.div>
          </motion.div>

          {/* --- HERO MOCKUP --- */}
          <motion.div
            initial={{ opacity: 0, y: 50, rotateX: 10 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="mt-20 relative mx-auto max-w-6xl rounded-xl border border-border bg-card/50 backdrop-blur-md shadow-2xl overflow-hidden aspect-[16/9] md:aspect-[21/9] group"
          >
            {/* Mock Window Header */}
            <div className="h-10 border-b border-border bg-muted/40 flex items-center px-4 gap-2">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-destructive/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
              </div>
              <div className="hidden md:flex ml-4 h-6 w-96 bg-background/50 border border-border/50 rounded-md items-center px-3 gap-2">
                <Lock className="w-3 h-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">codesense.ai/repo/vatsalumrania/codesense</span>
              </div>
            </div>

            {/* Mock Content */}
            <div className="flex h-full">
              {/* Sidebar */}
              <div className="w-64 border-r border-border bg-muted/10 p-4 space-y-4 hidden md:block text-left">
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-8 h-8 bg-primary/20 rounded flex items-center justify-center text-primary font-bold">F</div>
                  <span className="font-semibold text-sm">fastapi-repo</span>
                </div>
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-2 w-3/4 bg-muted-foreground/10 rounded animate-pulse" />
                  ))}
                </div>
              </div>

              {/* Chat Interface */}
              <div className="flex-1 p-6 md:p-12 flex flex-col items-center justify-center bg-background/50">
                <div className="text-center space-y-6 max-w-lg">
                  <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-2 border border-primary/20 shadow-inner">
                    <Bot className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="text-2xl md:text-3xl font-semibold tracking-tight">How can I help with your repo?</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div className="p-3 rounded-xl border border-border bg-card hover:bg-muted/50 hover:border-primary/30 cursor-pointer transition-all">
                      Explain the <span className="text-primary font-medium">auth flow</span>
                    </div>
                    <div className="p-3 rounded-xl border border-border bg-card hover:bg-muted/50 hover:border-primary/30 cursor-pointer transition-all">
                      Find <span className="text-primary font-medium">security leaks</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* --- SOCIAL PROOF --- */}
        <section className="py-12 border-y border-border bg-muted/20 mt-20">
          <div className="max-w-7xl mx-auto px-6 text-center">
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest mb-8">
              Built for Modern Engineering Teams
            </p>
            <div className="flex flex-wrap justify-center items-center gap-12 md:gap-20 opacity-50 grayscale hover:grayscale-0 transition-all duration-700">
              {/* Placeholder Logos (You can replace these with SVGs later) */}
              {["Acme Corp", "TechFlow", "DevScale", "OpenSource", "NextGen"].map((brand) => (
                <span key={brand} className="text-xl md:text-2xl font-bold flex items-center gap-2">
                  <div className="w-6 h-6 bg-current rounded-full opacity-20" /> {brand}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* --- HOW IT WORKS (Three Step) --- */}
        <section className="py-24 max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">From URL to Intelligence in Seconds</h2>
            <p className="text-muted-foreground">No complex setup. Just paste your repository link.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            {/* Connector Line (Desktop) */}
            <div className="hidden md:block absolute top-12 left-[20%] right-[20%] h-0.5 bg-gradient-to-r from-transparent via-border to-transparent z-0" />

            <StepCard
              number="01"
              title="Ingest"
              desc="Paste any public GitHub URL. CodeSense clones and parses the AST."
              icon={<Github className="w-6 h-6" />}
            />
            <StepCard
              number="02"
              title="Index"
              desc="We generate vector embeddings for every function and class using Gemini."
              icon={<Cpu className="w-6 h-6" />}
            />
            <StepCard
              number="03"
              title="Insight"
              desc="Start chatting, visualize the graph, or run an automated audit."
              icon={<Zap className="w-6 h-6" />}
            />
          </div>
        </section>

        {/* --- BENTO FEATURES --- */}
        <section className="max-w-7xl mx-auto px-6 py-24">
          <div className="mb-12">
            <h2 className="text-3xl md:text-5xl font-bold mb-6 tracking-tight">Everything you need to master code.</h2>
            <p className="text-muted-foreground text-lg max-w-2xl">
              CodeSense bridges the gap between static code and dynamic understanding using advanced RAG pipelines.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 grid-rows-2 gap-6 h-auto md:h-[600px]">

            {/* Card 1: RAG Chat */}
            <BentoCard
              className="md:col-span-2 md:row-span-2 bg-gradient-to-br from-primary/5 to-background border-primary/20"
              icon={<Bot className="w-8 h-8 text-primary" />}
              title="Context-Aware Chat"
              description="Ask questions like 'How does auth work?' and get answers grounded in your actual source code. No more hallucinations."
            >
              <div className="absolute bottom-0 right-0 w-[90%] h-[60%] bg-card border-t border-l border-border rounded-tl-3xl p-6 shadow-2xl transition-transform group-hover:-translate-y-2 duration-500">
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                      <span className="text-xs font-bold text-primary">U</span>
                    </div>
                    <div className="bg-muted p-3 rounded-2xl rounded-tl-none text-sm text-foreground w-full">
                      Where is the user validation logic?
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-primary-foreground" />
                    </div>
                    <div className="bg-primary/10 border border-primary/20 p-3 rounded-2xl rounded-tr-none text-sm text-foreground w-full">
                      It's in <code className="bg-background px-1 py-0.5 rounded text-xs border border-border">src/lib/auth.ts</code> inside the <code className="text-primary font-bold">validateUser</code> function.
                    </div>
                  </div>
                </div>
              </div>
            </BentoCard>

            {/* Card 2: Graph */}
            <BentoCard
              className="md:col-span-1 md:row-span-1"
              icon={<GitBranch className="w-8 h-8 text-blue-500" />}
              title="Dependency Visualizer"
              description="Interactive node graphs showing exactly how your modules import and depend on each other."
            />

            {/* Card 3: Audit */}
            <BentoCard
              className="md:col-span-1 md:row-span-1"
              icon={<ShieldCheck className="w-8 h-8 text-green-500" />}
              title="Automated Audits"
              description="Detect security vulnerabilities, API key leaks, and performance bottlenecks instantly."
            />
          </div>
        </section>

        {/* --- FAQ SECTION --- */}
        <section className="max-w-3xl mx-auto px-6 py-24">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {[
              { q: "Is my code secure?", a: "Yes. Repositories are cloned to a temporary ephemeral storage for analysis and deleted immediately after the session ends or upon request. We do not train models on your code." },
              { q: "Does it work with private repos?", a: "Currently, CodeSense supports public repositories. Private repository support via OAuth is coming in v2.0." },
              { q: "Which LLM do you use?", a: "We utilize Google's Gemini 1.5 Flash for its massive context window (1M tokens), allowing us to process entire codebases at once." },
              { q: "Is it free?", a: "CodeSense is open-source. You can run it locally for free using your own API keys, or use our hosted demo version." }
            ].map((item, i) => (
              <div key={i} className="border border-border rounded-lg overflow-hidden bg-card">
                <button
                  onClick={() => toggleFaq(i)}
                  className="w-full flex items-center justify-between p-4 text-left font-medium hover:bg-muted/50 transition-colors"
                >
                  {item.q}
                  <ChevronDown className={`w-4 h-4 transition-transform duration-300 ${openFaq === i ? "rotate-180" : ""}`} />
                </button>
                <AnimatePresence>
                  {openFaq === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="p-4 pt-0 text-muted-foreground text-sm leading-relaxed">
                        {item.a}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </section>

        {/* --- FINAL CTA --- */}
        <section className="py-24 px-6 text-center bg-gradient-to-b from-transparent to-primary/5">
          <div className="max-w-3xl mx-auto space-y-8">
            <h2 className="text-4xl md:text-5xl font-bold tracking-tighter">
              Ready to debug faster?
            </h2>
            <p className="text-muted-foreground text-lg">
              Join developers who are saving hours every week with CodeSense.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link href="/chat">
                <Button size="lg" className="h-14 px-10 rounded-full text-lg shadow-xl shadow-primary/20">
                  Get Started for Free
                </Button>
              </Link>
            </div>
            <p className="text-xs text-muted-foreground">No credit card required • Open Source</p>
          </div>
        </section>

        {/* --- FOOTER --- */}
        <footer className="border-t border-border bg-muted/20 pt-16 pb-8">
          <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div className="col-span-2 md:col-span-1 space-y-4">
              <div className="flex items-center gap-2">
                <div className="relative w-6 h-6">
                  <Image src="/logo.svg" alt="Logo" fill className="object-contain" />
                </div>
                <span className="font-bold">CodeSense</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Empowering developers with AI-driven insights for faster, safer, and smarter coding.
              </p>
            </div>

            <div>
              <h4 className="font-bold mb-4 text-sm">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="/chat" className="hover:text-primary">Chat</Link></li>
                <li><Link href="/graph" className="hover:text-primary">Visualizer</Link></li>
                <li><Link href="/audit" className="hover:text-primary">Audit</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-bold mb-4 text-sm">Resources</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#" className="hover:text-primary">Documentation</Link></li>
                <li><Link href="#" className="hover:text-primary">API Reference</Link></li>
                <li><Link href="https://github.com/vatsalumrania/codesense" className="hover:text-primary">GitHub</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-bold mb-4 text-sm">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><Link href="#" className="hover:text-primary">Privacy Policy</Link></li>
                <li><Link href="#" className="hover:text-primary">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="text-center border-t border-border pt-8">
            <p className="text-muted-foreground text-xs">© {new Date().getFullYear()} CodeSense. All rights reserved.</p>
          </div>
        </footer>

      </main>
    </div>
  );
}

// --- HELPER COMPONENTS ---

function BentoCard({ children, title, description, icon, className }: any) {
  return (
    <div className={`relative group overflow-hidden rounded-3xl border border-border bg-card p-8 hover:shadow-xl transition-all duration-300 flex flex-col ${className}`}>
      <div className="mb-4 p-3 bg-background w-fit rounded-xl border border-border shadow-sm text-primary">{icon}</div>
      <h3 className="text-2xl font-bold mb-2 tracking-tight">{title}</h3>
      <p className="text-muted-foreground leading-relaxed max-w-sm mb-8">{description}</p>
      {children}
    </div>
  );
}

function StepCard({ number, title, desc, icon }: any) {
  return (
    <div className="relative bg-card border border-border p-6 rounded-2xl z-10 hover:border-primary/50 transition-colors text-left group">
      <div className="absolute -top-4 -right-4 w-12 h-12 bg-muted rounded-full flex items-center justify-center font-bold text-muted-foreground border border-border group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
        {number}
      </div>
      <div className="mb-4 text-primary bg-primary/10 w-fit p-3 rounded-lg">{icon}</div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{desc}</p>
    </div>
  )
}