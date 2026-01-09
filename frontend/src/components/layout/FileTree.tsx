import { useState } from "react";
import { ChevronRight, ChevronDown, FileCode, Folder, Pin, PinOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileTreeProps {
  files: string[];
  pinnedFiles: string[];
  onTogglePin: (file: string) => void;
  onFileClick: (file: string) => void;
}

// Helper to build tree from flat paths
const buildTree = (paths: string[]) => {
  const tree: any = {};
  paths.forEach((path) => {
    const parts = path.split('/');
    let current = tree;
    parts.forEach((part) => {
      if (!current[part]) current[part] = {};
      current = current[part];
    });
  });
  return tree;
};

const TreeNode = ({ name, node, path, pinnedFiles, onTogglePin, onFileClick }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const isFile = Object.keys(node).length === 0;
  const fullPath = path ? `${path}/${name}` : name;
  const isPinned = pinnedFiles.includes(fullPath);

  if (isFile) {
    return (
      <div className="flex items-center justify-between group py-0.5 hover:bg-sidebar-accent/50 rounded-md px-2 cursor-pointer">
        <div 
            className="flex items-center gap-2 flex-1 min-w-0" 
            onClick={() => onFileClick(fullPath)}
        >
           <FileCode className="w-3.5 h-3.5 text-muted-foreground" />
           <span className="text-xs truncate text-sidebar-foreground/80 group-hover:text-sidebar-foreground">{name}</span>
        </div>
        <button 
            onClick={(e) => { e.stopPropagation(); onTogglePin(fullPath); }}
            className={cn(
                "opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-background",
                isPinned && "opacity-100 text-primary"
            )}
        >
            {isPinned ? <PinOff className="w-3 h-3" /> : <Pin className="w-3 h-3 text-muted-foreground" />}
        </button>
      </div>
    );
  }

  return (
    <div>
      <div 
        className="flex items-center gap-1.5 py-0.5 px-2 hover:bg-sidebar-accent/30 rounded-md cursor-pointer select-none"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground/70"/> : <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/70"/>}
        <Folder className="w-3.5 h-3.5 text-blue-500/70 fill-blue-500/20" />
        <span className="text-xs font-medium text-sidebar-foreground">{name}</span>
      </div>
      {isOpen && (
        <div className="pl-3 border-l border-sidebar-border/40 ml-2.5 mt-0.5">
          {Object.keys(node).map((childName) => (
            <TreeNode 
              key={childName} 
              name={childName} 
              node={node[childName]} 
              path={fullPath}
              pinnedFiles={pinnedFiles}
              onTogglePin={onTogglePin}
              onFileClick={onFileClick}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export function FileTree({ files, pinnedFiles, onTogglePin, onFileClick }: FileTreeProps) {
  const tree = buildTree(files);
  
  if (files.length === 0) return <div className="text-xs text-muted-foreground p-4">No files found.</div>;

  return (
    <div className="flex flex-col gap-0.5">
      {Object.keys(tree).map((name) => (
         <TreeNode 
            key={name} 
            name={name} 
            node={tree[name]} 
            path="" 
            pinnedFiles={pinnedFiles}
            onTogglePin={onTogglePin}
            onFileClick={onFileClick}
         />
      ))}
    </div>
  );
}