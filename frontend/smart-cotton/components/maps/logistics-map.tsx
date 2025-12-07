'use client'

import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { useEffect, useState, useRef } from 'react'

// --- Types ---
export interface VehicleInfo {
    id: number;
    plate_number: string;
    marker_color: string;
    status: string;
}

interface APIRoute {
    id: number;
    vehicle_info: VehicleInfo;
    coordinates: [number, number][];
    estimated_time: number;
}

// --- Math Utilities ---

// 1. Interpolation
function interpolate(start: [number, number], end: [number, number], t: number): [number, number] {
    const lat = start[0] + (end[0] - start[0]) * t;
    const lng = start[1] + (end[1] - start[1]) * t;
    return [lat, lng];
}

// 2. Bearing (Angle calculation for rotation) - ADDED THIS BACK
function getBearing(start: [number, number], end: [number, number]): number {
    const toRad = (d: number) => d * Math.PI / 180;
    const toDeg = (r: number) => r * 180 / Math.PI;
    const lat1 = toRad(start[0]), lat2 = toRad(end[0]);
    const dLon = toRad(end[1] - start[1]);
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

// 3. Icon Generator
const createTruckIcon = (rotation: number, color: string) => L.divIcon({
    html: `
      <div style="transform: rotate(${rotation}deg); transition: transform 0.1s linear; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="${color}" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 17h4V5H10v12zM20 17h2v-3.34a4 4 0 0 0-1.17-2.83L19 9h-5v8h6v2.83a4 4 0 0 0-1.17 2.83L19 19.83"/>
          <path d="M14 17h6"/>
          <circle cx="7.5" cy="17.5" r="2.5" fill="black"/>
          <circle cx="17.5" cy="17.5" r="2.5" fill="black"/>
        </svg>
      </div>`,
    className: 'custom-truck-icon',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
});

// --- Props Interface ---
interface LogisticsMapProps {
    onVehicleSelect?: (vehicle: VehicleInfo) => void;
}

export default function LogisticsMap({ onVehicleSelect }: LogisticsMapProps) {
    const [routes, setRoutes] = useState<APIRoute[]>([]);
    const [loading, setLoading] = useState(true);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [vehicleStates, setVehicleStates] = useState<Record<number, any>>({});
    const requestRef = useRef<number>(0);

    // --- 1. Fetch Data ---
    useEffect(() => {
        const fetchRoutes = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/logistics/map-data/`);
                if (!res.ok) throw new Error('Network error');

                const data: APIRoute[] = await res.json();
                setRoutes(data);

                // Initialize positions
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const initial: any = {};
                data.forEach(r => {
                    if (r.coordinates.length > 0) {
                        initial[r.vehicle_info.id] = {
                            pos: r.coordinates[0],
                            bearing: 0,
                            segmentIdx: 0,
                            t: 0
                        };
                    }
                });
                setVehicleStates(initial);
            } catch (err) {
                console.error("Failed to load routes:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchRoutes();
    }, []);

    // --- 2. Animation Loop ---
    const animate = () => {
        setVehicleStates(prev => {
            const next = { ...prev };

            routes.forEach(route => {
                const vid = route.vehicle_info.id;
                const state = prev[vid];

                if (!state || route.coordinates.length < 2) return;

                const SPEED = 0.0005;
                let newT = state.t + SPEED;
                let newSegment = state.segmentIdx;

                if (newT >= 1) {
                    newT = 0;
                    newSegment += 1;
                    if (newSegment >= route.coordinates.length - 1) {
                        newSegment = 0;
                    }
                }

                const startPoint = route.coordinates[newSegment];
                const endPoint = route.coordinates[newSegment + 1];

                next[vid] = {
                    pos: interpolate(startPoint, endPoint, newT),
                    bearing: getBearing(startPoint, endPoint), // Update rotation!
                    segmentIdx: newSegment,
                    t: newT
                };
            });
            return next;
        });

        requestRef.current = requestAnimationFrame(animate);
    };

    useEffect(() => {
        if (!loading && routes.length > 0) {
            requestRef.current = requestAnimationFrame(animate);
        }
        return () => {
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        };
    }, [loading, routes]);

    if (loading) return <div className="flex h-full w-full items-center justify-center bg-slate-50 text-slate-400">Loading Fleet Data...</div>;

    return (
        <MapContainer
            center={[41.2995, 69.2401]}
            zoom={12}
            zoomControl={false}
            style={{ height: "100%", width: "100%", borderRadius: "0.75rem" }}
        >
            <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            />

            {routes.map(route => {
                const vInfo = route.vehicle_info;
                const vState = vehicleStates[vInfo.id];

                return (
                    <div key={route.id}>
                        <Polyline
                            positions={route.coordinates}
                            pathOptions={{
                                color: vInfo.marker_color,
                                weight: 4,
                                opacity: 0.4,
                                lineCap: 'round'
                            }}
                        />

                        {vState && (
                            <Marker
                                position={vState.pos}
                                icon={createTruckIcon(vState.bearing, vInfo.marker_color)}
                                // --- Handle Click Here ---
                                eventHandlers={{
                                    click: () => {
                                        // 1. Send data to parent
                                        if (onVehicleSelect) onVehicleSelect(vInfo);
                                        // 2. Leaflet Popup will open automatically
                                    }
                                }}
                            >
                                <Popup className="custom-popup">
                                    <div className="p-1 min-w-[150px]">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-[10px] text-slate-400 font-bold uppercase">Vehicle</span>
                                            <div className={`w-2 h-2 rounded-full ${vInfo.status === 'MOVING' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`}></div>
                                        </div>

                                        <div className="text-base font-bold text-slate-800 leading-tight mb-1">{vInfo.plate_number}</div>

                                        <div className="bg-slate-50 p-2 rounded border border-slate-100 mt-2">
                                            <div className="flex justify-between text-xs text-slate-600 mb-1">
                                                <span>Status:</span>
                                                <span className="font-semibold text-blue-600">{vInfo.status}</span>
                                            </div>
                                            <div className="flex justify-between text-xs text-slate-600">
                                                <span>ETA:</span>
                                                <span className="font-semibold">{route.estimated_time} min</span>
                                            </div>
                                        </div>
                                    </div>
                                </Popup>
                            </Marker>
                        )}
                    </div>
                )
            })}
        </MapContainer>
    );
}