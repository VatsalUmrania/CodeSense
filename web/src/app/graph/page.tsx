"use client";

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  Panel,
  ReactFlowProvider,
  useReactFlow,
  Handle,
  Position,
  MarkerType,
  NodeProps
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Loader2, AlertCircle, Filter, Layers, Maximize2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { fileIcons } from "@/config/fileIcons"; // Using your existing icon config

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- 1. Custom Node Component ---
const FileNode = ({ data }: NodeProps) => {
  const fileName = data.label || "unknown";
  const ext = fileName.split('.').pop()?.toLowerCase() || "text";
  // Fallback icon if specific extension not found in your config
  const Icon = fileIcons[ext] || <FileText size={16} className="text-muted-foreground" />;

  return (
    <div className="relative group">
      {/* Input Handle */}
      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-2! h-2! bg-muted-foreground/50! border-none! transition-all group-hover:bg-primary!" 
      />
      
      {/* Node Body */}
      <div className="flex items-center gap-3 px-4 py-2.5 bg-card border border-border/60 shadow-sm rounded-xl min-w-[180px] max-w-[250px] transition-all duration-200 group-hover:border-primary/50 group-hover:shadow-md group-hover:-translate-y-0.5">
        <div className="shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
          {Icon}
        </div>
        <div className="flex flex-col min-w-0">
            <span className="text-xs font-semibold text-card-foreground truncate tracking-tight">
                {fileName}
            </span>
            {data.path && (
               <span className="text-[9px] text-muted-foreground truncate font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                  {data.path}
               </span>
            )}
        </div>
      </div>

      {/* Output Handle */}
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-2! h-2! bg-muted-foreground/50! border-none! transition-all group-hover:bg-primary!" 
      />
    </div>
  );
};

// Register custom types outside component
const nodeTypes = {
  file: FileNode,
};

// --- 2. Layout Engine ---
const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  
  dagreGraph.setGraph({ 
      rankdir: 'TB', 
      ranksep: 120,  // Vertical spacing between layers
      nodesep: 80    // Horizontal spacing between nodes
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 200, height: 60 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return {
    nodes: nodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      return {
        ...node,
        position: {
          x: nodeWithPosition.x - 100,
          y: nodeWithPosition.y - 30,
        },
      };
    }),
    edges,
  };
};

function GraphContent() {
  const searchParams = useSearchParams();
  const repoId = searchParams.get("id");
  const repoUrl = searchParams.get("url") || "";
  const { fitView } = useReactFlow();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  const [rawGraph, setRawGraph] = useState<{nodes: any[], edges: any[]}>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullView, setIsFullView] = useState(false);

  // Fetch Data
  useEffect(() => {
    if (!repoId) return;

    const fetchGraph = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_URL}/advanced/graph/${repoId}`);
            if (!res.ok) throw new Error(`Failed to fetch: ${res.statusText}`);
            
            const data = await res.json();
            if (data.nodes.length === 0) toast.warning("No dependency data found.");
            setRawGraph(data);
        } catch (e: any) {
            console.error(e);
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    fetchGraph();
  }, [repoId]);

  // Process & Layout Data
  useEffect(() => {
    if (rawGraph.nodes.length === 0) return;

    let filteredNodes = rawGraph.nodes;
    let filteredEdges = rawGraph.edges;

    // Filter Logic for "Main Flow"
    if (!isFullView) {
        const mainKeywords = ['page', 'layout', 'main', 'index', 'app', 'route', 'server', 'api'];
        const mainNodes = rawGraph.nodes.filter(n => {
            const label = (n.label || "").toLowerCase();
            return mainKeywords.some(kw => label.includes(kw));
        });

        if (mainNodes.length > 0) {
            const mainNodeIds = new Set(mainNodes.map(n => n.id));
            const childIds = new Set<string>();
            
            // Include immediate children to show context
            rawGraph.edges.forEach(e => {
                if (mainNodeIds.has(e.source)) childIds.add(e.target);
            });

            filteredNodes = rawGraph.nodes.filter(n => mainNodeIds.has(n.id) || childIds.has(n.id));
        }
    }

    // Filter edges based on visible nodes
    const visibleNodeIds = new Set(filteredNodes.map((n: any) => n.id));
    filteredEdges = rawGraph.edges.filter((e: any) => 
        visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
    );

    // Create React Flow Nodes
    const flowNodes: Node[] = filteredNodes.map((n: any) => ({
        id: n.id,
        type: 'file', // Use our custom type
        data: { label: n.label, path: n.id }, // Pass path for hover effect
        position: { x: 0, y: 0 }
    }));

    // Create React Flow Edges
    const flowEdges: Edge[] = filteredEdges.map((e: any, i: number) => ({
        id: `e${i}`,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: true,
        style: { stroke: 'var(--primary)', strokeWidth: 1.5, opacity: 0.6 },
        markerEnd: {
            type: MarkerType.ArrowClosed,
            color: 'var(--primary)',
        },
    }));

    const layouted = getLayoutedElements(flowNodes, flowEdges);
    setNodes(layouted.nodes);
    setEdges(layouted.edges);

    setTimeout(() => fitView({ duration: 800, padding: 0.2 }), 50);

  }, [rawGraph, isFullView, setNodes, setEdges, fitView]);

  return (
    <div className="flex h-screen w-full bg-background text-foreground font-sans">
      <AppSidebar isOpen={true} repoUrl={repoUrl} ingestStatus="success" messages={[]} onClear={() => {}} />
      
      <main className="flex-1 relative h-full bg-[#fafafa] dark:bg-black/20">
        
        {/* Loading / Error Overlays */}
        {loading && (
             <div className="absolute inset-0 flex items-center justify-center z-50 bg-background/80 backdrop-blur-sm">
                 <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-10 h-10 animate-spin text-primary" />
                    <span className="text-sm font-medium text-muted-foreground">Mapping Architecture...</span>
                 </div>
             </div>
        )}
        {!loading && error && (
            <div className="absolute inset-0 flex items-center justify-center z-40">
                <div className="bg-destructive/5 border border-destructive/20 p-6 rounded-xl flex flex-col items-center text-center max-w-md">
                    <AlertCircle className="w-8 h-8 text-destructive mb-3" />
                    <h3 className="font-semibold text-destructive">Graph Error</h3>
                    <p className="text-xs text-muted-foreground mt-1">{error}</p>
                </div>
            </div>
        )}

        {/* Control Panel */}
        <div className="absolute top-6 left-6 z-10 pointer-events-none">
            <div className="bg-background/95 backdrop-blur-xl border border-border/60 p-1 rounded-2xl shadow-2xl shadow-black/5 pointer-events-auto min-w-[320px] flex flex-col">
                
                <div className="p-4 border-b border-border/50">
                    <h1 className="text-sm font-semibold tracking-tight flex items-center gap-2 text-foreground/90">
                        <Layers className="w-4 h-4 text-primary"/> Project Architecture
                    </h1>
                    <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground font-mono uppercase tracking-wider">
                        <span className="flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 rounded-full bg-primary/50" />
                            {nodes.length} Modules
                        </span>
                        <span className="w-px h-3 bg-border"/>
                        <span className="flex items-center gap-1.5">
                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500/50" />
                            {edges.length} Connections
                        </span>
                    </div>
                </div>

                <div className="p-2 bg-muted/30 rounded-b-xl">
                    <div className="grid grid-cols-2 gap-1">
                        <Button 
                            size="sm" 
                            variant={!isFullView ? "default" : "ghost"} 
                            className={`h-8 text-xs shadow-none ${!isFullView ? 'bg-white text-black border border-black/5 dark:bg-zinc-800 dark:text-white hover:bg-white/90' : 'text-muted-foreground'}`}
                            onClick={() => setIsFullView(false)}
                        >
                            <Filter className="w-3 h-3 mr-2" /> Key Flows
                        </Button>
                        <Button 
                            size="sm" 
                            variant={isFullView ? "default" : "ghost"} 
                            className={`h-8 text-xs shadow-none ${isFullView ? 'bg-white text-black border border-black/5 dark:bg-zinc-800 dark:text-white hover:bg-white/90' : 'text-muted-foreground'}`}
                            onClick={() => setIsFullView(true)}
                        >
                            <Maximize2 className="w-3 h-3 mr-2" /> Full Map
                        </Button>
                    </div>
                </div>

            </div>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          minZoom={0.1}
          maxZoom={2}
          fitView
          proOptions={{ hideAttribution: true }}
          className="bg-dot-pattern" // Ensure you have a dot pattern class or use inline styles
        >
          <Background color="currentColor" gap={24} size={1} className="opacity-[0.03]" />
          <Controls className="bg-background border-border fill-foreground text-foreground shadow-sm rounded-lg overflow-hidden" showInteractive={false} />
          <MiniMap 
            className="bg-background border-border shadow-lg rounded-xl overflow-hidden m-6" 
            nodeColor="var(--primary)"
            maskColor="rgba(0, 0, 0, 0.05)"
          />
          <Panel position="bottom-center" className="mb-8">
             <div className="px-3 py-1.5 rounded-full bg-background/80 border border-border/50 backdrop-blur-sm text-[10px] text-muted-foreground font-medium shadow-sm">
                Scroll to zoom • Drag canvas to pan
             </div>
          </Panel>
        </ReactFlow>
      </main>
    </div>
  );
}

export default function GraphPage() {
    return (
        <ReactFlowProvider>
            <GraphContent />
        </ReactFlowProvider>
    );
}