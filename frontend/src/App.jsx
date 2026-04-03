import React, { useState } from "react";
import { useCompiler } from "./hooks/useCompiler";
import ActionCircle from "./components/ActionCircle";
import InspectorModal from "./components/InspectorModal";
import { Database, Play, Code } from "lucide-react";

function App() {
  const [sql, setSql] = useState("SELECT name FROM Students WHERE year = 3;");
  const { status, currentStage, compileData, executionData, error, compile, execute } = useCompiler();
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="h-screen w-full bg-slate-900 text-slate-100 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950">
        <h1 className="text-xl font-black tracking-tighter text-blue-400">
          SQL <span className="text-white">TO</span> PYTHON{" "}
          <span className="text-xs bg-blue-500/20 px-2 py-1 rounded text-blue-300">
            LALR ENGINE
          </span>
        </h1>
        {status === "SUCCESS" && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="text-blue-400 border border-blue-400/30 px-4 py-1.5 rounded-md text-xs font-bold hover:bg-blue-400/10 transition flex items-center gap-2"
          >
            <Code size={14} /> INSPECT STAGES
          </button>
        )}
      </header>

      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel: The Editor & SQL Terminal */}
        <div className="w-1/3 flex flex-col border-r border-slate-800">
          <div className="p-2 bg-slate-800 text-xs font-bold flex justify-between items-center">
            <span className="text-slate-400 uppercase">Input: Raw SQL</span>
            {status === "SUCCESS" && (
              <button 
                onClick={() => execute(sql)}
                className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded text-[10px] flex items-center gap-1 transition"
              >
                <Database size={12} /> RUN SQL
              </button>
            )}
          </div>
          <textarea
            className="flex-1 p-4 bg-slate-950 font-mono text-sm focus:outline-none resize-none"
            value={sql}
            onChange={(e) => setSql(e.target.value)}
          />
          
          {/* SQL Result Terminal */}
          {executionData && (
            <div className="h-1/3 bg-black border-t border-slate-800 p-4 font-mono text-[11px] overflow-auto">
              <div className="text-blue-400 font-bold mb-2 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" /> 
                POSTGRES_LIVE_OUTPUT
              </div>
              <pre className="text-slate-400">
                {JSON.stringify(executionData.sql_output, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Center: The Action Circle */}
        <div className="w-1/4 flex flex-col items-center justify-center bg-slate-900 z-10 border-r border-slate-800 shadow-2xl">
          <ActionCircle
            status={status}
            stage={currentStage}
            onClick={() => compile(sql)}
          />
        </div>

        {/* Right Panel: The Python Code & Compiled Terminal */}
        <div className="flex-1 flex flex-col">
          <div className="p-2 bg-slate-800 text-xs font-bold flex justify-between items-center">
            <span className="text-slate-400 uppercase">Output: Target Python Code</span>
            {status === "SUCCESS" && (
              <button 
                onClick={() => execute(sql)}
                className="bg-purple-600 hover:bg-purple-500 text-white px-3 py-1 rounded text-[10px] flex items-center gap-1 transition"
              >
                <Play size={12} /> RUN PYTHON
              </button>
            )}
          </div>
          
          <div className="flex-1 p-6 bg-slate-950 overflow-auto font-mono text-sm">
            {status === "ERROR" && (
              <div className="text-red-400 bg-red-950/30 p-4 border border-red-900/50 rounded">
                <h3 className="font-bold mb-2">Traceback (Compilation Failed):</h3>
                <pre className="whitespace-pre-wrap">{error}</pre>
              </div>
            )}
            {status === "SUCCESS" && (
              <pre className="text-blue-300 whitespace-pre-wrap">
                {compileData?.codegen}
              </pre>
            )}
            {status === "IDLE" && (
              <div className="text-slate-600 flex items-center justify-center h-full italic">
                Waiting for compilation start...
              </div>
            )}
          </div>

          {/* Python Result Terminal with Validation Logic */}
          {executionData && (
            <div className="h-1/3 bg-black border-t border-slate-800 p-4 font-mono text-[11px] overflow-auto">
              <div className="flex justify-between items-center mb-2">
                <div className="text-purple-400 font-bold flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" /> 
                  COMPILED_PYTHON_OUTPUT
                </div>
                <div className={`px-2 py-0.5 rounded text-[10px] font-bold ${executionData.is_valid ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                   {executionData.is_valid ? "VALIDATION: PASS" : "VALIDATION: FAIL"}
                </div>
              </div>
              <div className="text-[10px] text-slate-500 mb-2 italic">
                {executionData.message}
              </div>
              <pre className="text-slate-400">
                {JSON.stringify(executionData.python_output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </main>

      {isModalOpen && (
        <InspectorModal data={compileData} onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  );
}

export default App;