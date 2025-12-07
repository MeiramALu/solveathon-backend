"use client";

import React from 'react';
import { Worker } from '@/types/safety';

interface SafetyMapProps {
    workers: Worker[];
    selectedWorkerId: number | null;
    onSelectWorker: (workerId: number) => void;
}

export default function SafetyMap({ workers, selectedWorkerId, onSelectWorker }: SafetyMapProps) {
    const getNodeClass = (worker: Worker) => {
        if (worker.alert_panic || worker.alert_fall || worker.alert_environment) {
            return 'bg-red-500 border-red-600 animate-pulse shadow-lg shadow-red-500/50';
        }
        if (worker.alert_fatigue || worker.alert_acoustic || worker.alert_geofence) {
            return 'bg-yellow-500 border-yellow-600 shadow-md shadow-yellow-500/30';
        }
        return 'bg-green-500 border-green-600 shadow-md shadow-green-500/30';
    };

    return (
        <div className="relative w-full h-full bg-slate-100">
            {/* Grid Background */}
            <div
                className="absolute inset-0"
                style={{
                    backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px)',
                    backgroundSize: '40px 40px'
                }}
            />

            {/* Zones */}
            {/* Chemical Storage: Lat 20-55, Lon 20-55 */}
            <div
                className="absolute border-2 border-dashed border-red-400 rounded-xl bg-red-50 flex items-start justify-center pt-5"
                style={{
                    top: '20%',
                    left: '20%',
                    width: '35%',
                    height: '35%'
                }}
            >
                <span className="bg-white/90 px-3 py-1 rounded-lg text-xs text-red-700 font-semibold shadow-sm border border-red-200">
                    ⚗️ Chemical Storage
                </span>
            </div>

            {/* Assembly Line: Lat 25-55, Lon 65-95 */}
            <div
                className="absolute border-2 border-dashed border-blue-400 rounded-xl bg-blue-50 flex items-start justify-center pt-5"
                style={{
                    top: '25%',
                    left: '65%',
                    width: '30%',
                    height: '30%'
                }}
            >
                <span className="bg-white/90 px-3 py-1 rounded-lg text-xs text-blue-700 font-semibold shadow-sm border border-blue-200">
                    🏭 Assembly Line
                </span>
            </div>

            {/* Loading Dock: Lat 55-85, Lon 5-35 */}
            <div
                className="absolute border-2 border-dashed border-yellow-400 rounded-xl bg-yellow-50 flex items-start justify-center pt-5"
                style={{
                    top: '55%',
                    left: '5%',
                    width: '30%',
                    height: '30%'
                }}
            >
                <span className="bg-white/90 px-3 py-1 rounded-lg text-xs text-yellow-700 font-semibold shadow-sm border border-yellow-200">
                    🚚 Loading Dock
                </span>
            </div>

            {/* Worker Nodes */}
            {workers.map((worker) => (
                <button
                    key={worker.worker_id}
                    onClick={() => onSelectWorker(worker.worker_id)}
                    className="absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-1000 ease-in-out"
                    style={{
                        left: `${worker.longitude}%`,
                        top: `${worker.latitude}%`
                    }}
                >
                    {/* Dot */}
                    <div
                        className={`w-4 h-4 rounded-full border-2 ${getNodeClass(worker)} ${selectedWorkerId === worker.worker_id ? 'ring-4 ring-green-500/30 scale-150' : ''
                            }`}
                    />

                    {/* Label */}
                    <div className="absolute top-5 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                        <span className="bg-white px-2 py-0.5 rounded-lg text-xs text-slate-700 font-medium shadow-sm border border-slate-200">
                            {worker.name.split(' ')[0]}
                        </span>
                    </div>
                </button>
            ))}
        </div>
    );
}
