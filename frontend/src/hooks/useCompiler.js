import { useState } from "react";
import axios from "axios";

const API_BASE = "http://localhost:8000";

export const useCompiler = () => {
  const [status, setStatus] = useState("IDLE"); // IDLE, COMPILING, SUCCESS, ERROR
  const [currentStage, setCurrentStage] = useState(null);
  const [compileData, setCompileData] = useState(null);
  const [executionData, setExecutionData] = useState(null);
  const [error, setError] = useState(null);
  const [validationResult, setValidationResult] = useState(null);

  // 1. Compile Phase (Phases 1-6)
  const compile = async (sql) => {
    setStatus("COMPILING");
    // FIX: Use the variable to track progress
    setCurrentStage("LEXICAL ANALYSIS"); 
    
    try {
      const response = await axios.post(`${API_BASE}/compile`, { sql });
      
      // Simulate stage transitions for a cooler UI effect
      setCurrentStage("PARSING");
      setCurrentStage("SEMANTIC ANALYSIS");
      setCurrentStage("CODE GENERATION");
      
      setCompileData(response.data.stages);
      setStatus("SUCCESS");
      setCurrentStage("COMPILATION COMPLETE");
    } catch (err) {
      setStatus("ERROR");
      setCurrentStage("FAILED");
      setError(err.response?.data?.detail || "Compilation failed");
    }
  };

  // 2. Run SQL Phase (Ground Truth)
  const executeSql = async (sql) => {
    try {
      const response = await axios.post(`${API_BASE}/execute/sql`, { sql });
      setExecutionData((prev) => ({
        ...prev,
        sql_output: response.data.sql_output,
      }));
    } catch (err) {
      console.error("SQL Execution Error:", err);
    }
  };

  // 3. Run Python Phase (Compiled Logic + Validation)
  const executePython = async (sql) => {
    try {
      const response = await axios.post(`${API_BASE}/execute/python`, { sql });
      setExecutionData((prev) => ({
        ...prev,
        python_output: response.data.python_output,
        is_valid: response.data.is_valid,
        message: response.data.message,
      }));
    } catch (err) {
      console.error("Python Execution Error:", err);
    }
  };

  const validate = async (sqlData, pythonData) => {
    try {
      const response = await axios.post(`${API_BASE}/execute/validate`, {
        sql_data: sqlData,
        python_data: pythonData
      });
      setValidationResult(response.data);
    } catch (err) {
      console.error("Validation Error:", err);
    }
  };

  const resetExecution = () => {
    setExecutionData(null);
    setValidationResult(null); // Clear validation on new query
  };

  return {
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
  };
};