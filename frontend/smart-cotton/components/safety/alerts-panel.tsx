"use client";

import React, { useState, useEffect } from 'react';

interface Alert {
    id: number;
    alert_type: string;
    location: string;
    confidence: number;
    timestamp: string;
    detection_details?: {
        x?: number;
        y?: number;
        w?: number;
        h?: number;
    };
}

interface AlertsPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AlertsPanel({ isOpen, onClose }: AlertsPanelProps) {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchAlerts();
        }
    }, [isOpen]);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://smart-cotton-ai-system.onrender.com';
            const response = await fetch(`${API_BASE}/api/safety/alerts/`);
            const data = await response.json();
            setAlerts(data.slice(0, 20)); // Latest 20 alerts
        } catch (error) {
            console.error('Error fetching alerts:', error);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    const getAlertIcon = (type: string) => {
        if (type.includes('FIRE')) return '🔥';
        if (type.includes('HELMET')) return '⛑️';
        if (type.includes('DANGER')) return '⚠️';
        return '🚨';
    };

    const getAlertColor = (type: string) => {
        if (type.includes('FIRE')) return 'text-red-600 bg-red-50 border-red-200';
        if (type.includes('HELMET')) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
        return 'text-orange-600 bg-orange-50 border-orange-200';
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl border border-slate-200 w-full max-w-3xl max-h-[90vh] shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 lg:p-6 border-b border-slate-200 shrink-0">
                    <h2 className="text-2xl font-bold flex items-center gap-3 text-slate-800">
                        <span>🚨</span>
                        <span>Alert History</span>
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-800 text-3xl leading-none transition-colors"
                    >
                        ×
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-4 lg:p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : alerts.length === 0 ? (
                        <div className="text-center py-12 text-slate-500">
                            <p className="text-4xl mb-4">✅</p>
                            <p className="font-medium">No alerts recorded</p>
                            <p className="text-sm mt-1">System is running smoothly</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {alerts.map((alert) => (
                                <div
                                    key={alert.id}
                                    className={`p-3 lg:p-4 rounded-xl border ${getAlertColor(alert.alert_type)}`}
                                >
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex items-start gap-2 lg:gap-3 flex-1 min-w-0">
                                            <span className="text-xl lg:text-2xl shrink-0">{getAlertIcon(alert.alert_type)}</span>
                                            <div className="min-w-0 flex-1">
                                                <div className="font-semibold text-slate-800 text-sm lg:text-base wrap-break-word">
                                                    {alert.alert_type.replace(/_/g, ' ')}
                                                </div>
                                                <div className="text-xs lg:text-sm text-slate-600 mt-1 wrap-break-word">
                                                    📍 {alert.location}
                                                </div>
                                                <div className="text-xs text-slate-500 mt-1">
                                                    {new Date(alert.timestamp).toLocaleString()}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-xs font-mono bg-white px-2 py-1 rounded border border-slate-300 shrink-0">
                                            {(alert.confidence * 100).toFixed(1)}%
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 lg:p-6 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-3 shrink-0">
                    <button
                        onClick={fetchAlerts}
                        disabled={loading}
                        className="px-4 py-2 bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-200 transition-colors disabled:opacity-50"
                    >
                        🔄 Refresh
                    </button>
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-linear-to-r from-green-500 to-emerald-600 text-white rounded-lg font-semibold hover:opacity-90 transition-opacity shadow-sm"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
