"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Worker, RiskLevel, SimulationType } from '@/types/safety';
import WorkerSidebar from '@/components/safety/worker-sidebar';
import StatsBar from '@/components/safety/stats-bar';
import SafetyMap from '@/components/safety/safety-map';
import WorkerDetailsPanel from '@/components/safety/worker-details-panel';
import AIAnalysisModal from '@/components/safety/ai-analysis-modal';
import AlertsPanel from '@/components/safety/alerts-panel';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://smart-cotton-ai-system.onrender.com';

export default function SafetyMonitoringPage() {
    const [workers, setWorkers] = useState<Worker[]>([]);
    const [selectedWorkerId, setSelectedWorkerId] = useState<number | null>(null);
    const [riskLevel, setRiskLevel] = useState<RiskLevel>({
        level: 'LOW',
        percentage: 10,
        color: '#00ff9d'
    });
    const [isAIModalOpen, setIsAIModalOpen] = useState(false);
    const [aiAnalysis, setAIAnalysis] = useState<string>('');
    const [isLoadingAI, setIsLoadingAI] = useState(false);
    const [isAlertsPanelOpen, setIsAlertsPanelOpen] = useState(false);
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
    const [isMobileDetailsOpen, setIsMobileDetailsOpen] = useState(false);

    // Fetch workers data
    const fetchWorkers = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/safety/workers/live_status/`);
            const data = await response.json();

            setWorkers(data.workers);
            setRiskLevel(data.risk_level);

            // Auto-select first worker if none selected
            if (!selectedWorkerId && data.workers.length > 0) {
                setSelectedWorkerId(data.workers[0].worker_id);
            }
        } catch (error) {
            console.error('Error fetching workers:', error);
        }
    }, [selectedWorkerId]);

    // Poll for updates every second
    useEffect(() => {
        fetchWorkers();
        const interval = setInterval(fetchWorkers, 1000);
        return () => clearInterval(interval);
    }, [fetchWorkers]);

    // Get selected worker
    const selectedWorker = workers.find(w => w.worker_id === selectedWorkerId);

    // Trigger AI analysis
    const handleAICheck = async () => {
        if (!selectedWorker) return;

        setIsLoadingAI(true);
        setIsAIModalOpen(true);
        setAIAnalysis('Analyzing biometric patterns...');

        try {
            const response = await fetch(
                `${API_BASE}/api/safety/workers/${selectedWorker.worker_id}/ai_check/`
            );
            const data = await response.json();

            if (data.ai_analysis) {
                setAIAnalysis(data.ai_analysis);
            } else if (data.fallback_analysis) {
                setAIAnalysis(`Fallback Analysis:\n${data.fallback_analysis}`);
            } else {
                setAIAnalysis('Analysis unavailable');
            }
        } catch (error) {
            setAIAnalysis('Error performing AI analysis. Please try again.');
        } finally {
            setIsLoadingAI(false);
        }
    };

    // Trigger local analysis (non-AI)
    const handleLocalAnalysis = async () => {
        if (!selectedWorker) return;

        setIsLoadingAI(true);
        setIsAIModalOpen(true);
        setAIAnalysis('Running local safety analysis...');

        try {
            const response = await fetch(
                `${API_BASE}/api/safety/workers/${selectedWorker.worker_id}/local_analysis/`
            );
            const data = await response.json();

            const analysis = data.analysis;
            let analysisText = `🔍 LOCAL SAFETY ANALYSIS\n\n`;
            analysisText += `Worker: ${data.name}\n`;
            analysisText += `Status: ${analysis.safety_status}\n`;
            analysisText += `Zone: ${analysis.zone}\n\n`;
            analysisText += `🚨 ALERTS:\n`;
            analysisText += `• Panic: ${analysis.alert_panic ? '⚠️ YES' : '✅ No'}\n`;
            analysisText += `• Fall: ${analysis.alert_fall ? '⚠️ YES' : '✅ No'}\n`;
            analysisText += `• Fatigue: ${analysis.alert_fatigue ? '⚠️ YES' : '✅ No'}\n`;
            analysisText += `• Environment: ${analysis.alert_environment ? '⚠️ YES' : '✅ No'}\n`;
            analysisText += `• Acoustic: ${analysis.alert_acoustic ? '⚠️ YES' : '✅ No'}\n`;
            analysisText += `• Geofence: ${analysis.alert_geofence ? '⚠️ YES' : '✅ No'}\n`;

            setAIAnalysis(analysisText);
        } catch (error) {
            setAIAnalysis('Error performing local analysis. Please try again.');
        } finally {
            setIsLoadingAI(false);
        }
    };

    // Trigger simulation
    const handleSimulate = async (simType: SimulationType) => {
        if (!selectedWorker) return;

        if (simType === 'reset') {
            // Optionally handle reset logic here, or just refresh data
            fetchWorkers();
            return;
        }

        try {
            await fetch(`${API_BASE}/api/safety/workers/simulate/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: simType,
                    worker_id: selectedWorker.worker_id
                })
            });

            // Refresh data immediately
            fetchWorkers();
        } catch {
            console.error('Simulation error');
        }
    };

    return (
        <div className="h-full flex flex-col lg:flex-row bg-slate-50 overflow-hidden rounded-xl border border-slate-200 shadow-sm relative">
            {/* Mobile Header */}
            <div className="lg:hidden flex items-center justify-between p-4 bg-white border-b border-slate-200">
                <button
                    onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
                    className="px-3 py-2 bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-sm font-semibold hover:bg-slate-200 transition-colors flex items-center gap-2"
                >
                    <span>☰</span>
                    <span>Workers</span>
                </button>
                <h1 className="text-lg font-bold text-slate-800">🛡️ Safety Monitor</h1>
                {selectedWorker && (
                    <button
                        onClick={() => setIsMobileDetailsOpen(!isMobileDetailsOpen)}
                        className="px-3 py-2 bg-green-100 text-green-700 border border-green-300 rounded-lg text-sm font-semibold hover:bg-green-200 transition-colors"
                    >
                        Details
                    </button>
                )}
            </div>

            {/* Sidebar - Hidden on mobile by default, toggleable */}
            <div className={`${isMobileSidebarOpen ? 'fixed inset-0 z-40' : 'hidden'} lg:relative lg:flex`}>
                {/* Mobile overlay */}
                {isMobileSidebarOpen && (
                    <div
                        className="lg:hidden absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={() => setIsMobileSidebarOpen(false)}
                    />
                )}
                <div className={`${isMobileSidebarOpen ? 'absolute left-0 top-0 bottom-0 z-50' : ''} lg:relative`}>
                    <WorkerSidebar
                        workers={workers}
                        selectedWorkerId={selectedWorkerId}
                        onSelectWorker={(id) => {
                            setSelectedWorkerId(id);
                            setIsMobileSidebarOpen(false);
                        }}
                        onViewAlerts={() => setIsAlertsPanelOpen(true)}
                    />
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-h-0">
                {/* Stats Bar */}
                <StatsBar
                    workers={workers}
                    riskLevel={riskLevel}
                    onSimulate={handleSimulate}
                />

                {/* Map */}
                <div className="flex-1 relative overflow-hidden min-h-[400px]">
                    <SafetyMap
                        workers={workers}
                        selectedWorkerId={selectedWorkerId}
                        onSelectWorker={setSelectedWorkerId}
                    />
                </div>
            </div>

            {/* Details Panel - Hidden on mobile by default, toggleable */}
            {selectedWorker && (
                <div className={`${isMobileDetailsOpen ? 'fixed inset-0 z-40' : 'hidden'} lg:relative lg:flex`}>
                    {/* Mobile overlay */}
                    {isMobileDetailsOpen && (
                        <div
                            className="lg:hidden absolute inset-0 bg-black/50 backdrop-blur-sm"
                            onClick={() => setIsMobileDetailsOpen(false)}
                        />
                    )}
                    <div className={`${isMobileDetailsOpen ? 'absolute right-0 top-0 bottom-0 z-50 overflow-y-auto' : ''} lg:relative`}>
                        <WorkerDetailsPanel
                            worker={selectedWorker}
                            onAICheck={handleAICheck}
                            onLocalAnalysis={handleLocalAnalysis}
                            onClose={() => setIsMobileDetailsOpen(false)}
                        />
                    </div>
                </div>
            )}

            <AIAnalysisModal
                isOpen={isAIModalOpen}
                onClose={() => setIsAIModalOpen(false)}
                analysis={aiAnalysis}
                isLoading={isLoadingAI}
                workerName={selectedWorker?.name}
            />

            <AlertsPanel
                isOpen={isAlertsPanelOpen}
                onClose={() => setIsAlertsPanelOpen(false)}
            />
        </div>
    );
}
