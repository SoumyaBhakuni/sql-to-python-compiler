import React from 'react';
import { Play, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

const ActionCircle = ({ status, onClick }) => {
    const configs = {
        IDLE: { 
            color: 'bg-blue-600', 
            icon: <Play />, 
            label: "Ready to Compile" 
        },
        COMPILING: { 
            color: 'bg-yellow-500 animate-pulse', 
            icon: <Loader2 className="animate-spin" />, 
            label: "Compiling..." 
        },
        SUCCESS: { 
            color: 'bg-green-600', 
            icon: <CheckCircle />, 
            label: "Compilation Complete" 
        },
        ERROR: { 
            color: 'bg-red-600', 
            icon: <AlertCircle />, 
            label: "Compilation Failed" 
        }
    };

    const current = configs[status] || configs.IDLE;

    return (
        <div className="flex flex-col items-center justify-center gap-4">
            <button
                onClick={onClick}
                disabled={status === 'COMPILING'}
                className={`${current.color} w-32 h-32 rounded-full shadow-2xl flex items-center justify-center text-white transition-all duration-500 hover:scale-110 active:scale-95`}
            >
                {current.icon}
            </button>
            <div className="text-sm font-mono font-bold text-slate-400 tracking-widest uppercase">
                {current.label}
            </div>
        </div>
    );
};

export default ActionCircle;