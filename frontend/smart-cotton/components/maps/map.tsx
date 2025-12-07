'use client'

import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline, useMap, useMapEvents, CircleMarker } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { useEffect, useState } from 'react'
import { Map as MapIcon, Satellite } from 'lucide-react'

// --- Иконки ---
const iconUrl = 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png';
const iconRetinaUrl = 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png';
const shadowUrl = 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png';

const defaultIcon = L.icon({
    iconUrl,
    iconRetinaUrl,
    shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = defaultIcon;

// --- Специальная иконка грузовика (опционально, можно найти SVG) ---
const truckIcon = L.divIcon({
    html: `<div style="background-color: #f97316; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`,
    className: 'custom-truck-icon',
    iconSize: [12, 12],
    iconAnchor: [6, 6]
});

// --- Данные ---
const DATA = {
    water: {
        center: [41.2995, 69.2401] as [number, number],
        polygons: [
            { id: 1, coords: [[41.30, 69.24], [41.31, 69.24], [41.31, 69.25], [41.30, 69.25]] as [number, number][], color: 'blue', status: 'Humidity: 20% (Low)' },
            { id: 2, coords: [[41.29, 69.23], [41.30, 69.23], [41.30, 69.24], [41.29, 69.24]] as [number, number][], color: 'green', status: 'Humidity: 60% (Optimal)' }
        ]
    },
    // 🔥 ОБНОВЛЕННЫЕ ДАННЫЕ ЛОГИСТИКИ
    logistics: {
        center: [41.28, 69.22] as [number, number],
        routes: [
            { id: 'r1', coords: [[41.28, 69.22], [41.285, 69.23], [41.29, 69.24]] as [number, number][], color: '#f97316' }, // Orange route
            { id: 'r2', coords: [[41.25, 69.20], [41.26, 69.21], [41.27, 69.21]] as [number, number][], color: '#94a3b8' }  // Gray route
        ],
        trucks: [
            { id: 101, pos: [41.285, 69.23] as [number, number], info: 'Volvo FH16 (Cotton Bales) - Moving', status: 'moving' },
            { id: 102, pos: [41.27, 69.21] as [number, number], info: 'Kamaz 5490 (Raw Cotton) - Stopped', status: 'stopped' },
            { id: 103, pos: [41.25, 69.20] as [number, number], info: 'MAN TGX (Seeds) - Loading', status: 'loading' }
        ]
    },
    factory: {
        center: [41.25, 69.20] as [number, number],
        location: [41.25, 69.20] as [number, number]
    }
}

function MapEvents({ onClick }: { onClick?: (lat: number, lon: number) => void }) {
    useMapEvents({
        click(e) {
            if (onClick) onClick(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
}

interface MapProps {
    activeModule: string;
    onMapClick?: (lat: number, lon: number) => void; // New prop
    markers?: { lat: number; lon: number; color: string }[]; // New prop for analysis marker
}

export default function Map({ activeModule, onMapClick, markers }: MapProps) {
    const [mapMode, setMapMode] = useState<'satellite' | 'standard'>('standard'); // Для логистики лучше стандартная карта по умолчанию

    const mode = activeModule as keyof typeof DATA;
    const currentData = DATA[mode] || DATA.water;

    return (
        <div className="relative h-full w-full">
            <MapContainer
                key="main-map"
                center={currentData.center}
                zoom={12}
                zoomControl={false}
                style={{ height: "100%", width: "100%", borderRadius: "0.75rem" }}
            >
                {mapMode === 'satellite' ? (
                    <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" />
                ) : (
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                )}                
                <MapEvents onClick={onMapClick} />

                {markers?.map((m, idx) => (
                    <CircleMarker
                        key={idx}
                        center={[m.lat, m.lon]}
                        pathOptions={{ color: m.color, fillColor: m.color, fillOpacity: 0.8 }}
                        radius={10}
                    />
                ))}

                {/* --- RENDER LOGIC --- */}

                {/* {activeModule === 'water' && DATA.water.polygons.map(poly => (
                    <Polygon key={poly.id} positions={poly.coords} pathOptions={{ color: poly.color, fillOpacity: 0.4 }} />
                ))} */}

                {/* LOGISTICS: Маршруты и Грузовики */}
                {mode === 'logistics' && (
                    <>
                        {/* Рисуем линии маршрутов */}
                        {DATA.logistics.routes?.map(route => (
                            <Polyline
                                key={route.id}
                                positions={route.coords}
                                pathOptions={{ color: route.color, weight: 4, opacity: 0.7, dashArray: '10, 10' }}
                            />
                        ))}

                        {/* Рисуем грузовики */}
                        {DATA.logistics.trucks.map(truck => (
                            <Marker key={truck.id} position={truck.pos} icon={truckIcon}>
                                <Popup>
                                    <div className="font-bold">{truck.info}</div>
                                    <div className="text-xs text-slate-500">Speed: {truck.status === 'moving' ? '65 km/h' : '0 km/h'}</div>
                                </Popup>
                            </Marker>
                        ))}
                    </>
                )}

                {mode === 'factory' && (
                    <Marker position={DATA.factory.location}><Popup>Factory</Popup></Marker>
                )}
            </MapContainer>

            {/* Переключатель слоев */}
            <div className="absolute top-4 right-4 z-[1000] bg-white/90 backdrop-blur rounded-lg shadow-md border border-slate-200 p-1 flex flex-col gap-1">
                <button onClick={() => setMapMode('standard')} className={`p-2 rounded ${mapMode === 'standard' ? 'bg-slate-800 text-white' : 'text-slate-600'}`}><MapIcon className="w-5 h-5" /></button>
                <button onClick={() => setMapMode('satellite')} className={`p-2 rounded ${mapMode === 'satellite' ? 'bg-slate-800 text-white' : 'text-slate-600'}`}><Satellite className="w-5 h-5" /></button>
            </div>
        </div>
    )
}