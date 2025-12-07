"use client";

import React from 'react';
import { Worker } from '@/types/safety';

interface WorkerDetailsPanelProps {
    worker: Worker;
    onAICheck: () => void;
    onLocalAnalysis: () => void;
    onClose?: () => void;
}

export default function WorkerDetailsPanel({ worker, onAICheck, onLocalAnalysis, onClose }: WorkerDetailsPanelProps) {
    const getStatusBadgeClass = () => {
        if (worker.alert_panic || worker.alert_fall || worker.alert_environment) {
            return 'bg-red-500/20 text-red-500 border-red-500';
        }
        if (worker.alert_fatigue || worker.alert_acoustic || worker.alert_geofence) {
            return 'bg-yellow-500/20 text-yellow-500 border-yellow-500';
        }
        return 'bg-green-500/20 text-green-500 border-green-500';
    };

    const getStatusLabel = () => {
        if (worker.alert_panic || worker.alert_fall || worker.alert_environment) {
            return 'DANGER';
        }
        if (worker.alert_fatigue || worker.alert_acoustic || worker.alert_geofence) {
            return 'WARNING';
        }
        return 'OK';
    };

    return (
        <aside className="w-full lg:w-96 h-full bg-white border-l border-slate-200 overflow-y-auto">
            <div className="p-4 lg:p-6 space-y-4 lg:space-y-6">
                {/* Mobile Close Button */}
                {onClose && (
                    <button
                        onClick={onClose}
                        className="lg:hidden absolute top-4 right-4 w-8 h-8 flex items-center justify-center bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors"
                    >
                        ×
                    </button>
                )}

                {/* Profile Header */}
                <div>
                    <div className="flex items-center gap-4 mb-4">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                            src={`https://ui-avatars.com/api/?name=${encodeURIComponent(worker.name)}&background=334155&color=fff&size=128`}
                            alt={worker.name}
                            className="w-16 h-16 rounded-full border-2 border-slate-200"
                        />
                        <div className="flex-1">
                            <h2 className="text-xl font-bold text-slate-800">{worker.name}</h2>
                            <p className="text-sm text-slate-500">{worker.role} • ID: w{worker.worker_id}</p>
                        </div>
                    </div>

                    <div className={`inline-flex items-center px-3 py-1.5 rounded-lg border text-sm font-bold ${getStatusBadgeClass()}`}>
                        {getStatusLabel()}
                    </div>

                    <div className="flex flex-col sm:flex-row gap-2 mt-3">
                        <button
                            onClick={onAICheck}
                            className="flex-1 px-4 py-1.5 bg-linear-to-r from-green-500 to-emerald-600 text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity shadow-sm"
                        >
                            🧠 AI Check
                        </button>
                        <button
                            onClick={onLocalAnalysis}
                            className="flex-1 px-4 py-1.5 bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-200 transition-colors shadow-sm"
                        >
                            📊 Local Analysis
                        </button>
                    </div>
                </div>

                {/* Current Zone */}
                <div className="bg-slate-50 rounded-xl p-4 flex items-center gap-3 border border-slate-200">
                    <div className="text-2xl">📍</div>
                    <div>
                        <div className="text-xs text-slate-500 font-semibold">CURRENT ZONE</div>
                        <div className="font-semibold text-slate-800">{worker.zone}</div>
                    </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-4">
                    <MetricCard
                        label="HEART RATE"
                        value={`${worker.heart_rate.toFixed(1)}`}
                        unit="BPM"
                        icon="💓"
                        alert={worker.heart_rate > 110 || worker.heart_rate < 50}
                    />
                    <MetricCard
                        label="BLOOD OXYGEN"
                        value={`${worker.spo2}`}
                        unit="%"
                        icon="🫁"
                        alert={worker.spo2 < 90}
                    />
                    <MetricCard
                        label="TEMPERATURE"
                        value={`${worker.temp_c.toFixed(1)}`}
                        unit="°C"
                        icon="🌡️"
                        alert={worker.temp_c > 38}
                    />
                    <MetricCard
                        label="HRV"
                        value={`${worker.hrv.toFixed(0)}`}
                        unit="ms"
                        icon="📊"
                        alert={worker.hrv < 30}
                    />
                    <MetricCard
                        label="NOISE LEVEL"
                        value={`${worker.noise_level.toFixed(0)}`}
                        unit="dB"
                        icon="🔊"
                        alert={worker.noise_level > 85}
                    />
                    <MetricCard
                        label="STEPS"
                        value={`${worker.steps}`}
                        unit=""
                        icon="👣"
                    />
                </div>

                {/* Sleep/Readiness */}
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-xs text-slate-500 font-semibold">SLEEP SCORE</span>
                        <span className="text-lg font-bold text-slate-800">{worker.sleep_score}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                        <div
                            className="bg-linear-to-r from-green-500 to-emerald-600 h-2 rounded-full transition-all"
                            style={{ width: `${worker.sleep_score}%` }}
                        />
                    </div>
                </div>

                {/* Safety Status */}
                {worker.safety_status && worker.safety_status !== 'OK' && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                        <div className="text-sm font-semibold text-red-700 mb-2">⚠️ Active Alerts</div>
                        <div className="text-xs text-red-600 whitespace-pre-wrap">{worker.safety_status}</div>
                    </div>
                )}
            </div>
        </aside>
    );
}

interface MetricCardProps {
    label: string;
    value: string;
    unit: string;
    icon?: string;
    alert?: boolean;
}

function MetricCard({ label, value, unit, icon, alert }: MetricCardProps) {
    return (
        <div className={`bg-slate-50 rounded-xl p-4 border ${alert ? 'border-red-300 bg-red-50' : 'border-slate-200'}`}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-500 font-semibold">{label}</span>
                {icon && <span className="text-lg">{icon}</span>}
            </div>
            <div className="text-2xl font-bold text-slate-800">
                {value} <span className="text-sm text-slate-500">{unit}</span>
            </div>
        </div>
    );
}
