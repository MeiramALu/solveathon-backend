"use client";

import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useState } from "react";
import { MapIcon, Satellite } from "lucide-react";

// Fix Leaflet default icon issue
const iconUrl = "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png";
const iconRetinaUrl = "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png";
const shadowUrl = "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png";

const defaultIcon = L.icon({
    iconUrl,
    iconRetinaUrl,
    shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

interface WaterPoint {
    loc_x: number;
    loc_y: number;
    soil_humidity: number;
    pred_humidity: number | null;
    soil_temp: number;
    rain: number;
    air_temp: number;
    irrigation: number;
    days_since_irrigation: number;
    recommended_irrigation: number;
    dry_risk: number;
    risk_level: string;
    action: string;
    is_future: boolean;
}

interface WaterMapProps {
    points: WaterPoint[];
    onPointClick?: (point: WaterPoint) => void;
}

function MapBounds({ points }: { points: WaterPoint[] }) {
    const map = useMap();

    useEffect(() => {
        if (points.length > 0) {
            const bounds = L.latLngBounds(
                points.map((p) => [p.loc_y, p.loc_x] as [number, number])
            );
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [points, map]);

    return null;
}

export default function WaterMap({ points, onPointClick }: WaterMapProps) {
    const [mapMode, setMapMode] = useState<"satellite" | "standard">("standard");

    // Calculate center from points
    const center: [number, number] =
        points.length > 0
            ? [
                  points.reduce((sum, p) => sum + p.loc_y, 0) / points.length,
                  points.reduce((sum, p) => sum + p.loc_x, 0) / points.length,
              ]
            : [41.2995, 69.2401]; // Default Almaty region

    const getRiskColor = (riskLevel: string) => {
        switch (riskLevel) {
            case "high":
                return "#ef4444"; // red-500
            case "medium":
                return "#eab308"; // yellow-500
            default:
                return "#22c55e"; // green-500
        }
    };

    const getRadius = (action: string) => {
        return action === "IRRIGATE" ? 10 : 6;
    };

    return (
        <div className="relative h-full w-full">
            <MapContainer
                center={center}
                zoom={13}
                zoomControl={true}
                style={{ height: "600px", width: "100%", borderRadius: "0.5rem" }}
            >
                {mapMode === "satellite" ? (
                    <TileLayer
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        attribution="Esri"
                    />
                ) : (
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    />
                )}

                <MapBounds points={points} />

                {points.map((point, idx) => (
                    <CircleMarker
                        key={idx}
                        center={[point.loc_y, point.loc_x]}
                        radius={getRadius(point.action)}
                        pathOptions={{
                            color: "white",
                            weight: 2,
                            fillColor: getRiskColor(point.risk_level),
                            fillOpacity: 0.8,
                        }}
                        eventHandlers={{
                            click: () => onPointClick?.(point),
                        }}
                    >
                        <Popup>
                            <div className="text-sm">
                                <div className="font-bold mb-2">
                                    Location ({point.loc_x.toFixed(4)}, {point.loc_y.toFixed(4)})
                                </div>
                                <div className="space-y-1">
                                    <div>
                                        <strong>Soil Humidity:</strong> {point.soil_humidity.toFixed(1)}%
                                    </div>
                                    {point.pred_humidity && (
                                        <div>
                                            <strong>Predicted:</strong> {point.pred_humidity.toFixed(1)}%
                                        </div>
                                    )}
                                    <div>
                                        <strong>Risk Level:</strong>{" "}
                                        <span
                                            className={`font-semibold ${
                                                point.risk_level === "high"
                                                    ? "text-red-600"
                                                    : point.risk_level === "medium"
                                                    ? "text-yellow-600"
                                                    : "text-green-600"
                                            }`}
                                        >
                                            {point.risk_level.toUpperCase()}
                                        </span>
                                    </div>
                                    <div>
                                        <strong>Action:</strong>{" "}
                                        <span
                                            className={
                                                point.action === "IRRIGATE"
                                                    ? "text-blue-600 font-semibold"
                                                    : "text-gray-600"
                                            }
                                        >
                                            {point.action === "IRRIGATE" ? "💧 IRRIGATE" : "✓ SKIP"}
                                        </span>
                                    </div>
                                    <div>
                                        <strong>Recommend:</strong> {point.recommended_irrigation.toFixed(2)}{" "}
                                        m³/mu
                                    </div>
                                    <div>
                                        <strong>Soil Temp:</strong> {point.soil_temp.toFixed(1)}°C
                                    </div>
                                    <div>
                                        <strong>Air Temp:</strong> {point.air_temp.toFixed(1)}°C
                                    </div>
                                    <div>
                                        <strong>Days Since Irrigation:</strong> {point.days_since_irrigation}
                                    </div>
                                </div>
                                <button
                                    onClick={() => onPointClick?.(point)}
                                    className="mt-2 text-blue-600 hover:text-blue-800 text-xs font-semibold"
                                >
                                    View Time Series →
                                </button>
                            </div>
                        </Popup>
                    </CircleMarker>
                ))}
            </MapContainer>

            {/* Map Mode Toggle */}
            <div className="absolute top-4 right-4 z-[1000] bg-white/90 backdrop-blur rounded-lg shadow-md border border-slate-200 p-1 flex flex-col gap-1">
                <button
                    onClick={() => setMapMode("standard")}
                    className={`p-2 rounded ${
                        mapMode === "standard" ? "bg-slate-800 text-white" : "text-slate-600"
                    }`}
                    title="Standard Map"
                >
                    <MapIcon className="w-5 h-5" />
                </button>
                <button
                    onClick={() => setMapMode("satellite")}
                    className={`p-2 rounded ${
                        mapMode === "satellite" ? "bg-slate-800 text-white" : "text-slate-600"
                    }`}
                    title="Satellite View"
                >
                    <Satellite className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
