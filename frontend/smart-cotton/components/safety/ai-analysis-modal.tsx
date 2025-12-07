"use client";

import React from 'react';

interface AIAnalysisModalProps {
    isOpen: boolean;
    onClose: () => void;
    analysis: string;
    isLoading: boolean;
    workerName?: string;
}

export default function AIAnalysisModal({ isOpen, onClose, analysis, isLoading, workerName }: AIAnalysisModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl border border-slate-200 w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300">
                {/* Header */}
                <div className="flex items-center justify-between p-4 lg:p-6 border-b border-slate-200 shrink-0">
                    <h2 className="text-2xl font-bold flex items-center gap-3 text-slate-800">
                        <span>🧠</span>
                        <span>AI Safety Analysis</span>
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-800 text-3xl leading-none transition-colors"
                    >
                        ×
                    </button>
                </div>

                {/* Body */}
                <div className="p-4 lg:p-6 overflow-y-auto flex-1">
                    {workerName && (
                        <div className="mb-4 text-sm text-slate-500">
                            Analyzing: <span className="text-slate-800 font-semibold">{workerName}</span>
                        </div>
                    )}

                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="flex flex-col items-center gap-4">
                                <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
                                <p className="text-slate-500 text-center">Analyzing biometric patterns...</p>
                            </div>
                        </div>
                    ) : (
                            <div className="bg-slate-50 rounded-xl p-4 lg:p-6 text-slate-700 leading-relaxed whitespace-pre-wrap border border-slate-200 text-sm lg:text-base">
                            {analysis}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 lg:p-6 border-t border-slate-200 flex justify-end shrink-0">
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
