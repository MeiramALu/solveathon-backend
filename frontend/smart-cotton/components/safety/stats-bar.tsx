"use client";

import React from 'react';
import { Worker, RiskLevel, SimulationType } from '@/types/safety';

interface StatsBarProps {
    workers: Worker[];
    riskLevel: RiskLevel;
    onSimulate: (type: SimulationType) => void;
}

export default function StatsBar({ workers, riskLevel, onSimulate }: StatsBarProps) {
    // Calculate team fatigue (avg of 100 - sleep_score)
    const avgFatigue = workers.length > 0
        ? Math.round(workers.reduce((sum, w) => sum + (100 - w.sleep_score), 0) / workers.length)
        : 0;

    return (
        <header className="min-h-16 lg:h-20 bg-white border-b border-slate-200 flex flex-col lg:flex-row items-start lg:items-center justify-between px-4 lg:px-8 py-3 lg:py-0 gap-3 lg:gap-0">
            {/* Stats */}
            <div className="flex flex-wrap items-center gap-4 lg:gap-12 w-full lg:w-auto">
                {/* Team Fatigue */}
                <div className="flex items-center gap-2 lg:gap-4">
                    <div className="text-xl lg:text-2xl">💓</div>
                    <div>
                        <div className="text-xs text-slate-500 tracking-wider font-semibold">FATIGUE</div>
                        <div className="text-lg lg:text-xl font-bold text-slate-800">{avgFatigue}%</div>
                    </div>
                </div>

                {/* Active Crew */}
                <div className="flex items-center gap-2 lg:gap-4">
                    <div className="text-xl lg:text-2xl">👥</div>
                    <div>
                        <div className="text-xs text-slate-500 tracking-wider font-semibold">CREW</div>
                        <div className="text-lg lg:text-xl font-bold text-slate-800">{workers.length}</div>
                    </div>
                </div>

                {/* Site Risk Level */}
                <div className="flex items-center gap-2 lg:gap-4">
                    <div className="text-xl lg:text-2xl">⚠️</div>
                    <div>
                        <div className="text-xs text-slate-500 tracking-wider font-semibold">RISK</div>
                        <div className="text-lg lg:text-xl font-bold" style={{ color: riskLevel.color }}>
                            {riskLevel.level} <span className="hidden lg:inline">({riskLevel.percentage}%)</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Simulation Controls */}
            <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
                <span className="text-xs text-slate-500 tracking-wider font-semibold hidden lg:inline">SIMULATE:</span>
                <button
                    onClick={() => onSimulate('panic')}
                    className="px-2 lg:px-3 py-1.5 text-xs border border-slate-300 bg-white rounded-lg hover:border-red-500 hover:bg-red-50 hover:text-red-600 transition-colors font-medium text-slate-700"
                >
                    High HR
                </button>
                <button
                    onClick={() => onSimulate('toxic')}
                    className="px-2 lg:px-3 py-1.5 text-xs border border-slate-300 bg-white rounded-lg hover:border-purple-500 hover:bg-purple-50 hover:text-purple-600 transition-colors font-medium text-slate-700"
                >
                    Toxic
                </button>
                <button
                    onClick={() => onSimulate('fall')}
                    className="px-2 lg:px-3 py-1.5 text-xs border border-slate-300 bg-white rounded-lg hover:border-orange-500 hover:bg-orange-50 hover:text-orange-600 transition-colors font-medium text-slate-700"
                >
                    Fall
                </button>
                <button
                    onClick={() => onSimulate('reset')}
                    className="px-2 lg:px-3 py-1.5 text-xs border border-slate-300 bg-white rounded-lg hover:border-green-500 hover:bg-green-50 hover:text-green-600 transition-colors font-medium text-slate-700"
                >
                    Reset
                </button>
            </div>
        </header>
    );
}
