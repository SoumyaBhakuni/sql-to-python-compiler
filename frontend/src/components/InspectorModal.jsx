import React, { useState } from 'react';
import { X, Cpu, GitBranch, Workflow, Database, Code, Copy, Check, Zap } from 'lucide-react';

const InspectorModal = ({ data, onClose }) => {
  const [activeTab, setActiveTab] = useState('TOKENS');
  const [copySuccess, setCopySuccess] = useState(false);
  
  if (!data) return null;

  // Helper to copy code to clipboard
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-8">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-5xl h-full flex flex-col rounded-xl shadow-2xl overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
          <div className="flex gap-4 overflow-x-auto">
            <button 
              onClick={() => setActiveTab('TOKENS')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition whitespace-nowrap ${activeTab === 'TOKENS' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Cpu size={14} /> 1. LEXER
            </button>
            <button 
              onClick={() => setActiveTab('AST')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition whitespace-nowrap ${activeTab === 'AST' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <GitBranch size={14} /> 2. PARSER
            </button>
            <button 
              onClick={() => setActiveTab('IR')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition whitespace-nowrap ${activeTab === 'IR' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Workflow size={14} /> 3. PLANNER
            </button>
            <button 
              onClick={() => setActiveTab('OPTIMIZER')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition whitespace-nowrap ${activeTab === 'OPTIMIZER' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Zap size={14} /> 4. OPTIMIZER
            </button>
            <button 
              onClick={() => setActiveTab('CODEGEN')}
              className={`flex items-center gap-2 px-4 py-2 rounded text-xs font-bold transition whitespace-nowrap ${activeTab === 'CODEGEN' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Code size={14} /> 5. CODEGEN
            </button>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors ml-4 shrink-0">
            <X size={24} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-auto p-6 bg-slate-950 font-mono text-sm">
          
          {/* 1. LEXER TOKENS */}
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

          {/* 2. PARSER AST */}
          {activeTab === 'AST' && (
            <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                <pre className="text-green-400 leading-relaxed whitespace-pre-wrap">
                {JSON.stringify(data.parser, null, 2)}
                </pre>
            </div>
          )}

          {/* 3. RELATIONAL PLANNER */}
          {activeTab === 'IR' && (
            <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                <pre className="text-purple-400 leading-relaxed whitespace-pre-wrap">
                {JSON.stringify(data.planner, null, 2)}
                </pre>
            </div>
          )}

          {/* 4. OPTIMIZER */}
          {activeTab === 'OPTIMIZER' && (
            <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                <pre className="text-amber-400 leading-relaxed whitespace-pre-wrap">
                {JSON.stringify(data.optimizer, null, 2)}
                </pre>
            </div>
          )}

          {/* 5. PYTHON CODEGEN */}
          {activeTab === 'CODEGEN' && (
            <div className="relative group">
                <button 
                  onClick={() => copyToClipboard(data.codegen)}
                  className="absolute right-4 top-4 flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md border border-slate-700 transition-all z-10"
                >
                  {copySuccess ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
                  <span className="text-[10px] font-bold uppercase">{copySuccess ? 'Copied' : 'Copy Code'}</span>
                </button>
                <div className="bg-slate-900/50 p-6 rounded-lg border border-slate-800">
                    <pre className="text-blue-300 leading-relaxed whitespace-pre-wrap">
                    <code>{data.codegen}</code>
                    </pre>
                </div>
            </div>
          )}
        </div>
        
        {/* Modal Footer */}
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