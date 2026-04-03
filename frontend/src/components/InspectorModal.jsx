import React, { useState } from 'react';
// Changed 'TreeValue' to 'GitBranch' (great for ASTs) and 'Database'
import { X, Cpu, GitBranch, Workflow, Database } from 'lucide-react';

const InspectorModal = ({ data, onClose }) => {
  const [activeTab, setActiveTab] = useState('TOKENS');

  if (!data) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-8">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-5xl h-full flex flex-col rounded-xl shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <div className="flex gap-4">
            <button 
              onClick={() => setActiveTab('TOKENS')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition ${activeTab === 'TOKENS' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Cpu size={14} /> 1. LEXER TOKENS
            </button>
            <button 
              onClick={() => setActiveTab('AST')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition ${activeTab === 'AST' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <GitBranch size={14} /> 2. PARSER AST
            </button>
            <button 
              onClick={() => setActiveTab('IR')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition ${activeTab === 'IR' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Workflow size={14} /> 3. RELATIONAL IR
            </button>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors">
            <X size={24} />
          </button>
        </div>

        {/* Modal Content - Rest of the file remains the same */}
        <div className="flex-1 overflow-auto p-6 bg-slate-950 font-mono text-sm">
          {activeTab === 'TOKENS' && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
              {data.lexer.map((t, i) => (
                <div key={i} className="p-2 border border-slate-800 rounded bg-slate-900 flex flex-col">
                  <span className="text-blue-400 text-[10px] font-bold mb-1">{t.type}</span>
                  <span className="text-slate-200 truncate" title={t.value}>{t.value}</span>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'AST' && (
            <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                <pre className="text-green-400 leading-relaxed whitespace-pre-wrap">
                {JSON.stringify(data.parser, null, 2)}
                </pre>
            </div>
          )}

          {activeTab === 'IR' && (
            <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                <pre className="text-purple-400 leading-relaxed whitespace-pre-wrap">
                {JSON.stringify(data.planner, null, 2)}
                </pre>
            </div>
          )}
        </div>
        
        <div className="p-4 bg-slate-900 border-t border-slate-800 flex items-center justify-between">
            <div className="text-[10px] text-slate-500 italic uppercase tracking-widest">
                Compiler Phase Visualization Engine
            </div>
            <div className="flex items-center gap-2 text-blue-500 text-[10px] font-bold">
                <Database size={12} /> NEON POSTGRES CONNECTED
            </div>
        </div>
      </div>
    </div>
  );
};

export default InspectorModal;