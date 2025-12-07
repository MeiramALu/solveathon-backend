'use client'

import dynamic from 'next/dynamic'
import { Truck, AlertCircle, Activity } from 'lucide-react'
import { useEffect, useState } from 'react';
import VehicleModal from '@/components/logistics/vehicle-modal';

// Динамический импорт карты (отключаем SSR)
const LogisticsMap = dynamic(() => import('@/components/maps/logistics-map'), {
    ssr: false,
    loading: () => (
        <div className="h-full w-full bg-slate-100 flex items-center justify-center animate-pulse">
            <span className="text-slate-400 font-medium">Initializing Satellite Link...</span>
        </div>
    )
})

interface Vehicle {
    id: number;
    plate_number: string;
    status: string;
    marker_color: string;
}

export default function LogisticsPage() {
    const [vehicles, setVehicles] = useState<Vehicle[]>([]);
    const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchVehicles = async () => {
            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/logistics/vehicles/`);
                const data = await response.json();
                setVehicles(data);
            } catch (error) {
                console.error('Failed to fetch vehicles:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchVehicles();
    }, []);

    if (loading) {
        return <div>Loading vehicles...</div>;
    }

    return (
        <div className="relative w-full h-screen bg-slate-50 p-4">
            {/* Основной контейнер карты */}
            <div className="w-full h-full rounded-2xl overflow-hidden shadow-2xl border border-slate-200 relative">

                {/* Компонент Карты */}
                <LogisticsMap
                    onVehicleSelect={(vehicle) => {
                        setSelectedVehicle(vehicle);
                    }}
                />

                {/* 1. Верхний бар статистики */}
                <div className="absolute top-4 left-4 right-4 z-1000 flex justify-between pointer-events-none">
                    <div className="bg-white/90 backdrop-blur-md shadow-lg rounded-xl p-4 border border-slate-100 pointer-events-auto flex items-center gap-4">
                        <div className="bg-orange-100 p-2 rounded-lg">
                            <Truck className="w-6 h-6 text-orange-600" />
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-slate-800">Smart Logistics AI</h1>
                            <p className="text-xs text-slate-500">Live Fleet Tracking & Optimization</p>
                        </div>
                    </div>
                </div>

                {/* 2. Нижний левый угол - Статус транспортных средств */}
                <div className="absolute bottom-4 left-4 z-1000 space-y-3 pointer-events-none">
                    {vehicles.map((vehicle) => (
                        <div
                            key={vehicle.id}
                            className="bg-white/90 backdrop-blur-md shadow-lg rounded-xl p-3 border border-slate-100 pointer-events-auto flex items-center gap-3 w-64"
                        >
                            <div className={`w-3 h-3 rounded-full bg-[${vehicle.marker_color}]`} />
                            <div className="flex-1">
                                <h2 className="text-sm font-semibold text-slate-800">{vehicle.plate_number}</h2>
                                <p className="text-xs text-slate-500">Status: {vehicle.status}</p>
                            </div>
                            {vehicle.status === 'active' ? (
                                <Activity className="w-5 h-5 text-green-500" />
                            ) : (
                                <AlertCircle className="w-5 h-5 text-red-500" />
                            )}
                        </div>
                    ))}
                </div>
            </div>

            <VehicleModal
                vehicle={selectedVehicle}
                isOpen={!!selectedVehicle}
                onClose={() => setSelectedVehicle(null)}
            />
        </div>
    )
}