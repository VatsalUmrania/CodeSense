"use client";

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, ShieldAlert, Zap, AlertTriangle, CheckCircle, Terminal, Code2, Code } from "lucide-react";
import { toast } from "sonner";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AuditItem {
  severity: "High" | "Medium" | "Low";
  title: string;
  description: string;
  suggestion: string;
  code_fix?: string; // New field
}

export default function AuditPage() {
  const searchParams = useSearchParams();
  const repoId = searchParams.get("id");
  const repoUrl = searchParams.get("url") || "";
  
  const [report, setReport] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(false);

  const runAudit = async () => {
    if (!repoId) return;
    setLoading(true);
    try {
        const res = await fetch(`${API_URL}/advanced/audit/${repoId}`, { method: 'POST' });
        
        if (!res.ok) {
            throw new Error(`Audit failed: ${res.statusText}`);
        }

        const data = await res.json();
        
        if (Array.isArray(data)) {
            setReport(data);
        } else {
            console.error("Unexpected audit format:", data);
            toast.error("Received invalid data format from AI.");
            setReport([]); 
        }
    } catch (e) {
        console.error(e);
        toast.error("Failed to run audit. Ensure backend is running.");
        setReport([]); 
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-background text-foreground">
      <AppSidebar isOpen={true} repoUrl={repoUrl} ingestStatus="success" messages={[]} onClear={() => {}} />
      
      <main className="flex-1 relative h-full overflow-y-auto p-8 bg-muted/5">
         <div className="max-w-6xl mx-auto space-y-8">
            
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Code Audit</h1>
                    <p className="text-muted-foreground">AI-powered security and performance review</p>
                </div>
                <Button onClick={runAudit} disabled={loading}>
                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Zap className="mr-2 h-4 w-4" />}
                    {report.length > 0 ? "Re-Run Audit" : "Start Audit"}
                </Button>
            </div>

            {loading && (
                <div className="py-12 text-center animate-pulse">
                    <ShieldAlert className="w-12 h-12 text-primary mx-auto mb-4 opacity-50" />
                    <p className="text-sm text-muted-foreground">Analyzing codebase patterns...</p>
                </div>
            )}

            {!loading && report.length === 0 && (
                <div className="py-12 text-center border rounded-xl border-dashed border-border">
                    <p className="text-muted-foreground">Click "Start Audit" to analyze this repository.</p>
                </div>
            )}

            <div className="grid gap-6">
                {report.map((item, i) => (
                    <Card key={i} className="border-l-4 border-l-primary overflow-hidden">
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {item.severity === "High" ? <ShieldAlert className="text-red-500 h-5 w-5"/> : <AlertTriangle className="text-yellow-500 h-5 w-5"/>}
                                    <CardTitle className="text-base font-bold">{item.title}</CardTitle>
                                </div>
                                <span className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full border ${
                                    item.severity === "High" 
                                        ? "bg-red-500/10 text-red-600 border-red-200" 
                                        : "bg-yellow-500/10 text-yellow-600 border-yellow-200"
                                }`}>
                                    {item.severity}
                                </span>
                            </div>
                            <CardDescription className="mt-1">{item.description}</CardDescription>
                        </CardHeader>
                        
                        <CardContent className="bg-muted/30 p-0 border-t border-border/50">
                            <div className="p-4 space-y-4">
                                {/* Suggestion */}
                                <div className="flex gap-3">
                                    <CheckCircle className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                                    <div>
                                        <h4 className="text-sm font-semibold text-foreground mb-1">Suggestion</h4>
                                        <p className="text-sm text-muted-foreground leading-relaxed">{item.suggestion}</p>
                                    </div>
                                </div>

                                {/* Code Fix Block */}
                                {item.code_fix && (
                                    <div className="ml-8 rounded-md overflow-hidden border border-border/60 shadow-sm">
                                        <div className="bg-muted/50 px-3 py-1.5 border-b border-border/50 flex items-center gap-2">
                                            <Code className="w-3 h-3 text-muted-foreground" />
                                            <span className="text-[10px] font-mono text-muted-foreground font-medium">Proposed Fix</span>
                                        </div>
                                        <SyntaxHighlighter
                                            language="javascript"
                                            style={oneLight}
                                            customStyle={{ 
                                                margin: 0,  
                                                background: 'transparent', 
                                                fontSize: '13px', 
                                                lineHeight: '1.6',
                                                fontFamily: "var(--font-geist-mono), monospace",
                                            }}
                                            showLineNumbers={true}
                                            lineNumberStyle={{ 
                                                minWidth: "3.5em", 
                                                paddingRight: "1.5em", 
                                                color: "#52525b", 
                                                textAlign: "right",
                                                fontSize: '11px'
                                            }}
                                        >
                                        {item.code_fix}
                                    </SyntaxHighlighter>
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
         </div>
      </main>
    </div>
  );
}