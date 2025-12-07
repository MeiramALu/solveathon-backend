'use client'

import { X, Truck, Phone, Fuel, Gauge, MapPin, User } from 'lucide-react'
import { VehicleInfo } from '../maps/logistics-map'

interface VehicleModalProps {
    vehicle: VehicleInfo | null;
    isOpen: boolean;
    onClose: () => void;
}

export default function VehicleModal({ vehicle, isOpen, onClose }: VehicleModalProps) {
    if (!isOpen || !vehicle) return null;

    return (
        // 1. Backdrop (Затемненный фон)
        <div
            className="fixed inset-0 z-9999 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 transition-all duration-300"
            onClick={onClose} // Закрытие при клике на фон
        >
            {/* 2. Modal Container */}
            <div
                className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-200"
                onClick={(e) => e.stopPropagation()} // Чтобы клик внутри не закрывал окно
            >
                {/* Header */}
                <div className="bg-slate-50 p-4 border-b border-slate-100 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
                            <Truck className="w-6 h-6" style={{ color: vehicle.marker_color }} />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-slate-800">{vehicle.plate_number}</h2>
                            <p className="text-xs text-slate-500 font-medium tracking-wide uppercase">Heavy Truck • Volvo FH16</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-200 rounded-full transition-colors text-slate-400 hover:text-slate-600"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6">

                    {/* Status Badge */}
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-500 font-medium">Current Status</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2
                            ${vehicle.status === 'MOVING' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                            <span className={`w-2 h-2 rounded-full ${vehicle.status === 'MOVING' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`}></span>
                            {vehicle.status}
                        </span>
                    </div>

                    {/* Telemetry Grid (Mock Data for Demo) */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center gap-3">
                            <Gauge className="w-5 h-5 text-blue-500" />
                            <div>
                                <p className="text-[10px] text-slate-400 uppercase font-bold">Speed</p>
                                <p className="text-sm font-bold text-slate-700">65 km/h</p>
                            </div>
                        </div>
                        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center gap-3">
                            <Fuel className="w-5 h-5 text-orange-500" />
                            <div>
                                <p className="text-[10px] text-slate-400 uppercase font-bold">Fuel Lvl</p>
                                <p className="text-sm font-bold text-slate-700">74%</p>
                            </div>
                        </div>
                    </div>

                    {/* Driver Info Section */}
                    <div className="border-t border-slate-100 pt-4">
                        <h3 className="text-xs font-bold text-slate-400 uppercase mb-3">Driver Information</h3>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center text-slate-500">
                                    <User className="w-5 h-5" />
                                </div>
                                <div>
                                    {/* Здесь можно вывести реальное имя, если добавить его в API */}
                                    <p className="text-sm font-bold text-slate-800">Alisher B.</p>
                                    <p className="text-xs text-slate-500">ID: {vehicle.id}</p>
                                </div>
                            </div>
                            <button className="flex items-center gap-2 bg-green-50 text-green-600 px-3 py-2 rounded-lg text-xs font-bold hover:bg-green-100 transition">
                                <Phone className="w-3 h-3" />
                                Call Driver
                            </button>
                        </div>
                    </div>

                    {/* Location Info */}
                    <div className="bg-blue-50/50 p-3 rounded-xl border border-blue-100 flex gap-3 items-start">
                        <MapPin className="w-4 h-4 text-blue-500 mt-0.5" />
                        <div>
                            <p className="text-xs font-bold text-blue-700">En route to Tashkent Cargo Terminal</p>
                            <p className="text-[10px] text-blue-400 mt-0.5">Updated 2 seconds ago via GPS</p>
                        </div>
                    </div>
                </div>

                {/* Footer Buttons */}
                <div className="p-4 border-t border-slate-100 flex gap-3 bg-slate-50/50">
                    <button className="flex-1 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl text-sm font-bold hover:bg-slate-50 transition shadow-sm">
                        View History
                    </button>
                    <button className="flex-1 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-bold hover:bg-slate-800 transition shadow-lg shadow-slate-900/20">
                        Manage Cargo
                    </button>
                </div>
            </div>
        </div>
    )
}