import React from 'react';
import { Play, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

const ActionCircle = ({ status, stage, onClick }) => {
    const configs = {
        IDLE: { color: 'bg-blue-600', icon: <Play /> },
        COMPILING: { color: 'bg-yellow-500 animate-pulse', icon: <Loader2 className="animate-spin" /> },
        SUCCESS: { color: 'bg-green-600', icon: <CheckCircle /> },
        ERROR: { color: 'bg-red-600', icon: <AlertCircle /> }
    };

    const current = configs[status];

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
                {stage || "Ready to Compile"}
            </div>
        </div>
    );
};

export default ActionCircle;