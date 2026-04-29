import React, { useState, useEffect } from "react";
import { useCompiler } from "./hooks/useCompiler";
import ActionCircle from "./components/ActionCircle";
import InspectorModal from "./components/InspectorModal";
import { Database, Play, Code, CheckCircle, AlertCircle } from "lucide-react";

function App() {
  const [sql, setSql] = useState("SELECT \"Students\".\"name\" FROM \"Students\" WHERE \"Students\".\"year\" = 3;");
  const { 
    status, 
    currentStage, 
    compileData, 
    executionData, 
    error, 
    compile, 
    executeSql,    
    executePython, 
    validationResult,
    validate,
    resetExecution
  } = useCompiler();
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false); // Gatekeeper state
  
  return (
    <div className="h-screen w-full bg-slate-900 text-slate-100 flex flex-col overflow-hidden font-sans">
      {/* Header */}
      <header className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950 shadow-md">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-black tracking-tighter text-blue-400">
            SQL <span className="text-white">TO</span> PYTHON{" "}
            <span className="text-[10px] bg-blue-500/20 px-2 py-1 rounded text-blue-300 ml-2 border border-blue-500/30">
              LALR ENGINE v2.0
            </span>
          </h1>
        </div>
        
        <div className="flex items-center gap-3">
          {status === "SUCCESS" && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="text-blue-400 border border-blue-400/30 px-4 py-1.5 rounded-md text-xs font-bold hover:bg-blue-400/10 transition flex items-center gap-2"
            >
              <Code size={14} /> INSPECT STAGES
            </button>
          )}
          <div className={`h-2 w-2 rounded-full ${status === 'SUCCESS' ? 'bg-green-500' : status === 'ERROR' ? 'bg-red-500' : 'bg-slate-600'}`} />
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel: SQL Editor & SQL Output */}
        <div className="w-1/3 flex flex-col border-r border-slate-800 bg-slate-950">
          <div className="p-2 bg-slate-900/50 text-[10px] font-bold flex justify-between items-center border-b border-slate-800">
            <span className="text-slate-500 uppercase tracking-widest">Input: Raw SQL Query</span>
            {status === "SUCCESS" && (
              <button 
                disabled={isLoading}
                onClick={async () => {
                  setIsLoading(true);
                  try {
                    await executeSql(sql);
                  } finally {
                    setIsLoading(false);
                  }
                }}
                className={`bg-blue-600 text-white px-3 py-1 rounded-sm text-[10px] font-bold flex items-center gap-1.5 transition shadow-lg ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-500'}`}
              >
                <Database size={12} /> {isLoading ? "RUNNING..." : "RUN SQL"}
              </button>
            )}
          </div>
          <textarea
            className="flex-1 p-6 bg-slate-950 font-mono text-sm focus:outline-none resize-none text-blue-100/90 leading-relaxed"
            value={sql}
            spellCheck="false"
            onChange={(e) => setSql(e.target.value)}
          />
          
          {/* SQL Result Terminal (Persistent Header) */}
          <div className="h-1/3 bg-black border-t border-slate-800 flex flex-col">
            <div className="p-2 bg-slate-900/30 border-b border-white/5 flex items-center justify-between">
               <div className="text-blue-400 font-bold text-[10px] flex items-center gap-2 uppercase tracking-tight">
                <div className={`w-1.5 h-1.5 rounded-full ${executionData?.sql_output ? 'bg-blue-500 animate-pulse' : 'bg-slate-700'}`} /> 
                Postgres Live Output
              </div>
            </div>
            <div className="flex-1 p-4 font-mono text-[11px] overflow-auto text-slate-400">
              {executionData?.sql_output ? (
                <pre>{JSON.stringify(executionData.sql_output, null, 2)}</pre>
              ) : (
                <span className="text-slate-700 italic">No SQL execution data...</span>
              )}
            </div>
          </div>
        </div>

        {/* Center: The Action Circle (The Compiler Core) */}
        <div className="w-80 flex flex-col items-center justify-center bg-slate-900 z-10 border-r border-slate-800 shadow-2xl relative">
          <div className="absolute top-4 text-[10px] text-slate-500 font-bold uppercase tracking-widest">Compiler Core</div>
          <ActionCircle
            status={status}
            stage={currentStage}
            onClick={() => {
              resetExecution();
              compile(sql);
            }}
          />
        </div>

        {/* Right Panel: Target Python Code & Compiled Terminal */}
        <div className="flex-1 flex flex-col bg-slate-950">
          <div className="p-2 bg-slate-900/50 text-[10px] font-bold flex justify-between items-center border-b border-slate-800">
            <span className="text-slate-500 uppercase tracking-widest">Output: Generated Python Plan</span>
            {status === "SUCCESS" && (
              <button 
                disabled={isLoading}
                onClick={async () => {
                  if (status === "SUCCESS") {
                    setIsLoading(true);
                    try {
                      await executePython(sql);
                    } finally {
                      setIsLoading(false);
                    }
                  }
                }}
                className={`bg-purple-600 text-white px-3 py-1 rounded-sm text-[10px] font-bold flex items-center gap-1.5 transition shadow-lg ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-purple-500'}`}
              >
                <Play size={12} /> {isLoading ? "EXECUTING..." : "RUN PYTHON"}
              </button>
            )}
          </div>
          
          <div className="flex-1 p-6 bg-slate-950 overflow-auto font-mono text-sm">
            {status === "ERROR" && (
              <div className="text-red-400 bg-red-950/20 p-4 border border-red-900/30 rounded">
                <div className="flex items-center gap-2 mb-2 text-red-500 font-bold text-xs">
                  <AlertCircle size={14} /> COMPILATION_FAILED
                </div>
                <pre className="whitespace-pre-wrap text-xs opacity-80">{error}</pre>
              </div>
            )}
            {status === "SUCCESS" && (
              <pre className="text-blue-300/90 whitespace-pre-wrap leading-relaxed">
                {compileData?.codegen}
              </pre>
            )}
            {status === "IDLE" && (
              <div className="text-slate-700 flex flex-col items-center justify-center h-full gap-2">
                <Code size={40} className="opacity-10" />
                <span className="text-xs italic tracking-widest uppercase">Ready to compile...</span>
              </div>
            )}
          </div>

          {/* Python Result Terminal with Enhanced Validation Badge */}
          <div className="h-1/3 bg-black border-t border-slate-800 flex flex-col">
            <div className="p-2 bg-slate-900/30 border-b border-white/5 flex justify-between items-center">
              <div className="text-purple-400 font-bold text-[10px] flex items-center gap-2 uppercase tracking-tight">
                <div className={`w-1.5 h-1.5 rounded-full ${executionData?.python_output ? 'bg-purple-500 animate-pulse' : 'bg-slate-700'}`} /> 
                Compiled Python Output
              </div>

              <div className="flex items-center gap-2">
                {executionData?.sql_output && executionData?.python_output && !validationResult && (
                  <button 
                    onClick={() => validate(executionData.sql_output, executionData.python_output)}
                    className="bg-green-600 hover:bg-green-500 text-white px-3 py-1 rounded-sm text-[9px] font-black uppercase transition-all hover:scale-105"
                  >
                    Compare Results
                  </button>
                )}

                {validationResult && (
                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded text-[9px] font-black uppercase border ${validationResult.is_valid ? 'bg-green-500/10 text-green-400 border-green-500/30' : 'bg-red-500/10 text-red-400 border-red-500/30'}`}>
                    {validationResult.is_valid ? <CheckCircle size={10}/> : <AlertCircle size={10}/>}
                    {validationResult.is_valid ? "VALIDATION: PASS" : "VALIDATION: FAIL"}
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 p-4 font-mono text-[11px] overflow-auto text-slate-400">
              {executionData?.python_output ? (
                <>
                  {validationResult && (
                    <div className="text-[10px] text-slate-500 mb-3 pb-2 border-b border-white/5 flex justify-between">
                      <span>{validationResult.message}</span>
                      <span className="text-slate-600">Rows: {executionData.python_output.length}</span>
                    </div>
                  )}
                  <pre>{JSON.stringify(executionData.python_output, null, 2)}</pre>
                </>
              ) : (
                <span className="text-slate-700 italic">No Python execution data...</span>
              )}
            </div>
          </div>
        </div>
      </main>

      {isModalOpen && (
        <InspectorModal data={compileData} onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  );
}

export default App;