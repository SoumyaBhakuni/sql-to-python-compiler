import React, { useState, useCallback } from 'react';
import { X, Cpu, GitBranch, Workflow, Database, Code, Copy, Check, Zap, GitMerge, FileJson } from 'lucide-react';
import Tree from 'react-d3-tree';

// 1. Hook to perfectly center the tree dynamically
const useCenteredTree = () => {
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const containerRef = useCallback((containerElem) => {
    if (containerElem !== null) {
      const { width } = containerElem.getBoundingClientRect();
      setTranslate({ x: width / 2, y: 50 });
    }
  }, []);
  return [translate, containerRef];
};

// 2. Deep Recursive JSON to D3-Tree Adapter
const transformToD3Tree = (node) => {
  if (!node) return { name: "null" };
  if (typeof node !== 'object') return { name: String(node) };

  let name = node.node_type || node.op || "Node";
  let attributes = {};
  let children = [];

  if (node.op) {
    if (node.params) {
      Object.entries(node.params).forEach(([k, v]) => {
        if (v !== null && v !== undefined) {
          if (typeof v === 'object') {
            children.push({ name: `Param: ${k}`, children: [transformToD3Tree(v)] });
          } else {
            attributes[k] = String(v);
          }
        }
      });
    }
    if (node.source) children.push({ name: "[Source]", children: [transformToD3Tree(node.source)] });
    if (node.left) children.push({ name: "[Left]", children: [transformToD3Tree(node.left)] });
    if (node.right) children.push({ name: "[Right]", children: [transformToD3Tree(node.right)] });
  } 
  else if (node.node_type) {
    Object.entries(node).forEach(([key, value]) => {
      if (key === 'node_type') return;
      if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) return;

      if (typeof value === 'object') {
        if (Array.isArray(value)) {
          const arrayChildren = value.map((item) => transformToD3Tree(item));
          children.push({ name: key, children: arrayChildren });
        } else {
          children.push({ name: key, children: [transformToD3Tree(value)] });
        }
      } else {
        attributes[key] = String(value);
      }
    });
  } 
  else {
    Object.entries(node).forEach(([key, value]) => {
      if (value === null || value === undefined) return;
      if (typeof value === 'object') {
         children.push({ name: key, children: [transformToD3Tree(value)] });
      } else {
         attributes[key] = String(value);
      }
    });
  }

  return {
    name,
    attributes: Object.keys(attributes).length > 0 ? attributes : undefined,
    children: children.length > 0 ? children : undefined
  };
};

// --- THE FIX: Upgraded Interactive Node Renderer ---
const renderCustomNode = ({ nodeDatum, toggleNode }) => {
  // react-d3-tree stores hidden children in `_children` when collapsed
  const hasVisibleChildren = nodeDatum.children && nodeDatum.children.length > 0;
  const hasHiddenChildren = nodeDatum._children && nodeDatum._children.length > 0;
  const isExpandable = hasVisibleChildren || hasHiddenChildren;

  return (
    // Moving the onClick to the entire <g> group makes the text clickable too!
    <g onClick={toggleNode} className="cursor-pointer group">
      <circle 
        r="15" 
        fill={isExpandable ? "#3b82f6" : "#10b981"} 
        className="transition-colors group-hover:opacity-80" 
      />
      
      {/* The +/- Indicator */}
      {isExpandable && (
        <text fill="#ffffff" x="0" y="5" textAnchor="middle" fontSize="16" fontWeight="bold">
          {hasHiddenChildren ? "+" : "-"}
        </text>
      )}

      {/* Node Name */}
      <text fill="#1e293b" strokeWidth="0" x="20" dy="-5" fontSize="14" fontWeight="bold">
        {nodeDatum.name}
      </text>
      
      {/* Node Attributes */}
      {nodeDatum.attributes && Object.entries(nodeDatum.attributes).map(([key, val], i) => (
        <text key={key} fill="#64748b" strokeWidth="0" x="20" dy={14 + (i * 12)} fontSize="10">
          {key}: <tspan fill="#ea580c">{val}</tspan>
        </text>
      ))}
    </g>
  );
};

// 3. TreeViewer Component
const TreeViewer = ({ jsonTree }) => {
  const [viewMode, setViewMode] = useState('TREE');
  const [translate, containerRef] = useCenteredTree();

  return (
    <div className="w-full h-[600px] bg-slate-950/80 rounded-lg border border-slate-800 relative flex flex-col overflow-hidden">
      <style>{`
        .rd3t-link { stroke: #cbd5e1 !important; stroke-width: 2px !important; }
      `}</style>

      <div className="flex justify-between items-center bg-slate-900/90 border-b border-slate-800 p-2 z-10">
        <span className="text-[10px] font-bold text-blue-400 px-2 flex items-center gap-2">
          {viewMode === 'TREE' ? <><GitMerge size={14}/> VISUAL TREE</> : <><FileJson size={14}/> RAW JSON</>}
        </span>
        <div className="flex bg-slate-800 rounded p-1">
          <button
            onClick={() => setViewMode('TREE')}
            className={`px-3 py-1 rounded text-xs font-bold transition-colors ${viewMode === 'TREE' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            TREE
          </button>
          <button
            onClick={() => setViewMode('JSON')}
            className={`px-3 py-1 rounded text-xs font-bold transition-colors ${viewMode === 'JSON' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            JSON
          </button>
        </div>
      </div>

      <div className="flex-1 relative w-full h-full bg-slate-50"> 
        {viewMode === 'TREE' ? (
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }} ref={containerRef}>
            <Tree 
              data={transformToD3Tree(jsonTree)} 
              orientation="vertical"
              pathFunc="step"
              translate={translate}
              renderCustomNodeElement={renderCustomNode}
              separation={{ siblings: 2, nonSiblings: 2 }}
              initialDepth={1} // <-- THE FIX: Starts the tree cleanly collapsed!
            />
          </div>
        ) : (
          <div className="absolute inset-0 overflow-auto p-4 bg-slate-950">
            <pre className="text-emerald-400/80 text-xs leading-relaxed whitespace-pre-wrap">
              {JSON.stringify(jsonTree, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

// 4. Main Component
const InspectorModal = ({ data, onClose }) => {
  const [activeTab, setActiveTab] = useState('TOKENS');
  const [copySuccess, setCopySuccess] = useState(false);
  
  if (!data) return null;

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy!', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 md:p-8">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-5xl h-full flex flex-col rounded-xl shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <div className="flex gap-2 overflow-x-auto">
            {['TOKENS', 'AST', 'IR', 'OPTIMIZER', 'CODEGEN'].map((tab) => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition whitespace-nowrap ${activeTab === tab ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
              >
                {tab === 'TOKENS' && <Cpu size={14} />}
                {tab === 'AST' && <GitBranch size={14} />}
                {tab === 'IR' && <Workflow size={14} />}
                {tab === 'OPTIMIZER' && <Zap size={14} />}
                {tab === 'CODEGEN' && <Code size={14} />}
                {tab}
              </button>
            ))}
          </div>
          
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors shrink-0 ml-4">
            <X size={24} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-auto p-6 bg-slate-950 font-mono text-sm relative">
          
          {activeTab === 'TOKENS' && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
              {data.lexer?.map((t, i) => (
                <div key={i} className="p-2 border border-slate-800 rounded bg-slate-900 flex flex-col">
                  <span className="text-blue-400 text-[10px] font-bold mb-1">{t.type}</span>
                  <span className="text-slate-200 truncate" title={t.value}>{t.value}</span>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'AST' && <TreeViewer jsonTree={data.parser} />}
          {activeTab === 'IR' && <TreeViewer jsonTree={data.planner} />}
          {activeTab === 'OPTIMIZER' && <TreeViewer jsonTree={data.optimizer} />}

          {activeTab === 'CODEGEN' && (
            <div className="relative group h-full">
                <button 
                  onClick={() => copyToClipboard(data.codegen)}
                  className="absolute right-4 top-4 flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md border border-slate-700 transition-all z-10"
                >
                  {copySuccess ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                  <span className="text-[10px] font-bold uppercase">{copySuccess ? 'Copied' : 'Copy Code'}</span>
                </button>
                <div className="bg-slate-900/50 p-6 rounded-lg border border-slate-800 min-h-full">
                    <pre className="text-blue-300 leading-relaxed whitespace-pre-wrap">
                    <code>{data.codegen}</code>
                    </pre>
                </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InspectorModal;