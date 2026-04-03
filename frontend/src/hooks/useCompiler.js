import { useState } from 'react';
import axios from 'axios';

const API_BASE = "http://localhost:8000";

export const useCompiler = () => {
    const [status, setStatus] = useState('IDLE'); // IDLE, COMPILING, SUCCESS, ERROR
    const [currentStage, setCurrentStage] = useState('');
    const [compileData, setCompileData] = useState(null);
    const [error, setError] = useState(null);
    const [executionData, setExecutionData] = useState(null);

    const compile = async (sql) => {
        setStatus('COMPILING');
        setError(null);
        
        try {
            // Artificial delays can be added here to make the 
            // "Action Circle" transitions visible for the Viva demo
            setCurrentStage('LEXICAL ANALYSING...');
            const res = await axios.post(`${API_BASE}/compile`, { sql });
            
            setCompileData(res.data.stages);
            setStatus('SUCCESS');
            setCurrentStage('COMPILATION COMPLETE');
        } catch (err) {
            setStatus('ERROR');
            setError(err.response?.data?.detail || "Unknown Compiler Error");
            setCurrentStage('ERROR DETECTED');
        }
    };

    const execute = async (sql) => {
    try {
        const res = await axios.post(`${API_BASE}/execute`, { sql });
        setExecutionData(res.data);
    } catch (err) {
        setError(err.response?.data?.detail || "Execution Error");
    }
    };

    return { status, currentStage, compileData, executionData, error, compile, execute };
};