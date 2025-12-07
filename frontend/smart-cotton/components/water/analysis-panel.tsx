import { SmartPlan } from '@/service/water-service';
import { AlertCircle, Droplets, Sun, Info } from 'lucide-react';

interface AnalysisPanelProps {
    plan: SmartPlan | null;
    loading: boolean;
}

export default function AnalysisPanel({ plan, loading }: AnalysisPanelProps) {
    if (loading) {
        return (
            <div className="absolute top-4 left-4 z-1000 w-80 bg-white/90 backdrop-blur rounded-xl shadow-lg border border-slate-200 p-6 flex flex-col items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
                <p className="text-slate-500 text-sm">Analyzing Satellite Data...</p>
            </div>
        );
    }

    if (!plan) {
        return (
            <div className="absolute top-4 left-4 z-1000 w-80 bg-white/90 backdrop-blur rounded-xl shadow-lg border border-slate-200 p-6 text-center">
                <Droplets className="w-10 h-10 text-blue-400 mx-auto mb-3" />
                <h3 className="font-semibold text-slate-800">Select a Field</h3>
                <p className="text-xs text-slate-500 mt-1">Click anywhere on the map to calculate drought risk and irrigation needs.</p>
            </div>
        );
    }

    const { drought, irrigation, location } = plan;
    const riskColor = drought.level === 'low' ? 'bg-green-500' : drought.level === 'medium' ? 'bg-yellow-500' : 'bg-red-500';

    return (
        <div className="absolute top-4 left-4 z-1000 w-96 bg-white/95 backdrop-blur rounded-xl shadow-xl border border-slate-200 overflow-hidden max-h-[90vh] overflow-y-auto">

            {/* Header */}
            <div className="p-4 border-b border-slate-100 bg-slate-50">
                <div className="flex justify-between items-center mb-1">
                    <h2 className="font-bold text-slate-800">Field Analysis</h2>
                    <span className={`${riskColor} text-white text-[10px] font-bold px-2 py-1 rounded-full uppercase`}>
                        {drought.level} Risk
                    </span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono">
                    Lat: {location.lat.toFixed(4)} • Lon: {location.lon.toFixed(4)}
                </div>
            </div>

            <div className="p-4 space-y-6">

                {/* Irrigation Recommendation */}
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                    <h3 className="text-xs font-bold text-blue-800 uppercase mb-3 flex items-center gap-2">
                        <Droplets className="w-4 h-4" /> Irrigation Plan
                    </h3>
                    <div className="flex justify-between items-end mb-2">
                        <span className="text-slate-600 text-sm">Recommended Dose</span>
                        <span className="text-2xl font-bold text-blue-700">{irrigation.recommended_mm} <span className="text-sm font-normal text-slate-500">mm</span></span>
                    </div>
                    <div className="flex justify-between items-end">
                        <span className="text-slate-600 text-sm">Estimated Duration</span>
                        <span className="text-lg font-bold text-slate-800">{irrigation.recommended_minutes} <span className="text-sm font-normal text-slate-500">mins</span></span>
                    </div>
                    <div className="flex justify-between items-end">
                        <span className="text-slate-600 text-sm">Irrigation Priority</span>
                        <span className="text-lg font-bold text-slate-800">{irrigation.priority.toFixed(2)}</span>
                    </div>
                    <div className="mt-3 text-[11px] text-blue-600/80 leading-relaxed">
                        For <strong>{irrigation.explanation.crop}</strong> at the <strong>{irrigation.explanation.growthStage}</strong> stage, under current drought conditions (<strong>{irrigation.explanation.droughtLevel.toUpperCase()}</strong>), this location should receive <strong>{irrigation.recommended_mm} mm</strong> of water (approximately <strong>{irrigation.recommended_minutes} minutes</strong> with the current system).
                    </div>
                </div>

                {/* Drought Indicators */}
                <div>
                    <h3 className="text-xs font-bold text-slate-400 uppercase mb-3">Water Balance (30 Days)</h3>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between p-2 bg-slate-50 rounded">
                            <span className="text-slate-600">Precipitation</span>
                            <span className="font-medium text-black">{drought.indicators.P30.toFixed(1)} mm</span>
                        </div>
                        <div className="flex justify-between p-2 bg-slate-50 rounded">
                            <span className="text-slate-600">Evaporation (ET₀)</span>
                            <span className="font-medium text-black">{drought.indicators.ET30.toFixed(1)} mm</span>
                        </div>
                        <div className="flex justify-between p-2 bg-slate-100 border-l-4 border-slate-400 rounded-r">
                            <span className="font-bold text-slate-700">Net Balance</span>
                            <span className={`font-bold ${drought.indicators.waterBalance < 0 ? 'text-red-500' : 'text-green-600'}`}>
                                {drought.indicators.waterBalance.toFixed(1)} mm
                            </span>
                        </div>
                    </div>
                </div>

                {/* Forecast */}
                <div>
                    <h3 className="text-xs font-bold text-slate-400 uppercase mb-3">7-Day Forecast</h3>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 bg-orange-50 rounded border border-orange-100 flex flex-col items-center">
                            <Sun className="w-5 h-5 text-orange-400 mb-1" />
                            <span className="text-lg font-bold text-slate-700">{drought.indicators.forecastTmax.toFixed(0)}°C</span>
                            <span className="text-[10px] text-slate-500">Max Temp</span>
                        </div>
                        <div className="p-3 bg-blue-50 rounded border border-blue-100 flex flex-col items-center">
                            <AlertCircle className="w-5 h-5 text-blue-400 mb-1" />
                            <span className="text-lg font-bold text-slate-700">{drought.indicators.forecastPrecip.toFixed(1)}</span>
                            <span className="text-[10px] text-slate-500">Rain (mm)</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}