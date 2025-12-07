"use client";

import React from 'react';
import { Worker } from '@/types/safety';

interface WorkerSidebarProps {
    workers: Worker[];
    selectedWorkerId: number | null;
    onSelectWorker: (workerId: number) => void;
    onViewAlerts: () => void;
}

export default function WorkerSidebar({ workers, selectedWorkerId, onSelectWorker, onViewAlerts }: WorkerSidebarProps) {
    const getStatusColor = (worker: Worker) => {
        if (worker.alert_panic || worker.alert_fall || worker.alert_environment) {
            return 'text-red-500';
        }
        if (worker.alert_fatigue || worker.alert_acoustic || worker.alert_geofence) {
            return 'text-yellow-500';
        }
        return 'text-green-500';
    };

    const getStatusLabel = (worker: Worker) => {
        if (worker.alert_panic || worker.alert_fall || worker.alert_environment) {
            return 'DANGER';
        }
        if (worker.alert_fatigue || worker.alert_acoustic || worker.alert_geofence) {
            return 'WARNING';
        }
        return 'OK';
    };

    return (
        <aside className="w-full lg:w-72 h-full bg-white border-r border-slate-200 flex flex-col p-4 lg:p-5">
            {/* Brand */}
            <div className="mb-4 lg:mb-6">
                <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                    <span className="text-2xl">🛡️</span>
                    Safety AI System
                </h1>
                <p className="text-slate-500 text-sm mt-1">Real-time Worker Monitoring</p>

                <button
                    onClick={onViewAlerts}
                    className="w-full mt-3 px-3 py-2 bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-200 transition-colors flex items-center justify-center gap-2"
                >
                    🚨 View Alert History
                </button>
            </div>

            {/* Worker List */}
            <div className="flex-1 overflow-y-auto space-y-2">
                {workers.map((worker) => (
                    <button
                        key={worker.worker_id}
                        onClick={() => onSelectWorker(worker.worker_id)}
                        className={`w-full flex items-center gap-2 lg:gap-3 p-2 lg:p-3 rounded-xl border transition-all ${selectedWorkerId === worker.worker_id
                            ? 'bg-white border-green-600 shadow-md ring-1 ring-green-600'
                            : 'bg-white border-slate-200 hover:border-green-300 hover:shadow-sm'
                            }`}
                    >
                        {/* Avatar */}
                        <div className={`p-2 rounded-lg ${selectedWorkerId === worker.worker_id ? 'bg-green-50' : 'bg-slate-50'
                            }`}>
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                                src={`https://ui-avatars.com/api/?name=${encodeURIComponent(worker.name)}&background=334155&color=fff&size=32`}
                                alt={worker.name}
                                className="w-8 h-8 rounded-full"
                            />
                        </div>

                        {/* Info */}
                        <div className="flex-1 text-left">
                            <div className="text-sm font-semibold text-slate-800">{worker.name}</div>
                            <div className="text-xs text-slate-500">{worker.role}</div>
                        </div>

                        {/* Status Badge */}
                        <div className={`text-xs font-bold ${getStatusColor(worker)}`}>
                            {getStatusLabel(worker)}
                        </div>
                    </button>
                ))}
            </div>
        </aside>
    );
}
