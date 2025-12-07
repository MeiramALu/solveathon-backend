"use client";

import React, { useState, useEffect } from "react";
import { waterService } from "@/service/water-service";
import dynamic from "next/dynamic";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

const LeafletMap = dynamic(() => import("@/components/maps/water-map"), {
    ssr: false,
    loading: () => (
        <div className="h-[600px] bg-gray-100 rounded-lg flex items-center justify-center">
            <p className="text-gray-600">Loading map...</p>
        </div>
    ),
});

interface MapPoint {
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

interface DateInfo {
    date: string;
    avg_pred: number;
    risk_count: number;
    point_count: number;
}

export default function WaterManagementPage() {
    const [fieldId, setFieldId] = useState<number>(1);
    const [availableDates, setAvailableDates] = useState<string[]>([]);
    const [selectedDate, setSelectedDate] = useState<string>("");
    const [lastObservedDate, setLastObservedDate] = useState<string>("");
    const [mapPoints, setMapPoints] = useState<MapPoint[]>([]);
    const [dateSummaries, setDateSummaries] = useState<DateInfo[]>([]);
    const [drynessThreshold, setDrynessThreshold] = useState<number | undefined>(
        undefined
    );
    const [selectedLocation, setSelectedLocation] = useState<MapPoint | null>(
        null
    );
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [timeSeriesData, setTimeSeriesData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (fieldId) {
            loadAvailableDates();
            loadDateSummaries();
        }
    }, [fieldId]);

    useEffect(() => {
        if (selectedDate) {
            loadMapData();
        }
    }, [selectedDate, drynessThreshold]);

    const loadAvailableDates = async () => {
        try {
            const data = await waterService.getAvailableDates(fieldId);
            // Filter dates to only show up to 2024-09-22
            const filteredDates = (data.dates || []).filter((date: string) => date <= "2024-09-22");
            setAvailableDates(filteredDates);
            setLastObservedDate(data.last_observed_date || "");
            if (filteredDates.length > 0) {
                setSelectedDate(filteredDates[filteredDates.length - 1]);
            }
        } catch (err) {
            console.error("Failed to load dates:", err);
        }
    };

    const loadMapData = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await waterService.getMapData(
                fieldId,
                selectedDate,
                drynessThreshold
            );
            setMapPoints(data.points || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load map data");
        } finally {
            setLoading(false);
        }
    };

    const loadDateSummaries = async () => {
        try {
            const data = await waterService.getDateSummary(fieldId);
            setDateSummaries(data.dates || []);
        } catch (err) {
            console.error("Failed to load date summaries:", err);
        }
    };

    const loadLocationTimeSeries = async (locX: number, locY: number) => {
        try {
            const data = await waterService.getLocationTimeSeries(fieldId, locX, locY);
            setTimeSeriesData(data);
        } catch (err) {
            console.error("Failed to load time series:", err);
        }
    };

    const handleLocationClick = (point: MapPoint) => {
        setSelectedLocation(point);
        loadLocationTimeSeries(point.loc_x, point.loc_y);
    };

    const generatePredictions = async () => {
        setLoading(true);
        setError(null);
        try {
            await waterService.bulkGeneratePredictions(fieldId, selectedDate);
            await loadMapData();
            await loadDateSummaries();
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to generate predictions"
            );
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (riskLevel: string) => {
        switch (riskLevel) {
            case "high":
                return "bg-red-100 text-red-800 border-red-300";
            case "medium":
                return "bg-yellow-100 text-yellow-800 border-yellow-300";
            default:
                return "bg-green-100 text-green-800 border-green-300";
        }
    };

    const isObservedDate = selectedDate <= lastObservedDate;
    const isFutureDate = !isObservedDate && selectedDate !== "";

    const overviewStats = {
        totalPoints: mapPoints.length,
        avgHumidity:
            mapPoints.length > 0
                ? (
                    mapPoints.reduce((sum, p) => sum + (p.pred_humidity || 0), 0) /
                    mapPoints.length
                ).toFixed(1)
                : "0",
        highRisk: mapPoints.filter((p) => p.dry_risk === 1).length,
        needsIrrigation: mapPoints.filter((p) => p.action === "IRRIGATE").length,
        totalIrrigation: mapPoints
            .reduce((sum, p) => sum + p.recommended_irrigation, 0)
            .toFixed(1),
    };

    return (
        <div className="bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h1 className="text-3xl font-bold text-gray-900 mb-4">
                        💧 Water Management & Irrigation Intelligence
                    </h1>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Field ID
                            </label>
                            <input
                                type="number"
                                value={fieldId}
                                onChange={(e) => setFieldId(Number(e.target.value))}
                                className="border border-gray-300 rounded-md px-4 py-2 w-full"
                                min="1"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Date
                            </label>
                            <select
                                value={selectedDate}
                                onChange={(e) => setSelectedDate(e.target.value)}
                                className="border border-gray-300 rounded-md px-4 py-2 w-full"
                            >
                                {availableDates.map((date) => (
                                    <option key={date} value={date}>
                                        {date} {date === lastObservedDate && "(Last Observed)"}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Dryness Filter (≤ {drynessThreshold ? `${drynessThreshold}%` : "All"})
                            </label>
                            <input
                                type="range"
                                value={drynessThreshold || 100}
                                onChange={(e) => {
                                    const value = Number(e.target.value);
                                    setDrynessThreshold(value === 100 ? undefined : value);
                                }}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                min="0"
                                max="100"
                                step="10"
                            />
                            <div className="flex justify-between text-xs text-gray-500 mt-1">
                                <span>0%</span>
                                <span>20%</span>
                                <span>40%</span>
                                <span>60%</span>
                                <span>80%</span>
                                <span>All</span>
                            </div>
                        </div>
                        <div className="flex items-end">
                            <button
                                onClick={generatePredictions}
                                disabled={loading}
                                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 transition w-full"
                            >
                                🤖 Generate Predictions
                            </button>
                        </div>
                    </div>

                    {/* Date Type Indicator */}
                    {selectedDate && (
                        <div className="mt-4">
                            {isFutureDate ? (
                                <div className="bg-purple-100 border border-purple-300 rounded-md px-4 py-2 text-purple-800">
                                    🔮 <strong>Future Prediction</strong> - AI simulated data for{" "}
                                    {selectedDate}
                                </div>
                            ) : (
                                <div className="bg-blue-100 border border-blue-300 rounded-md px-4 py-2 text-blue-800">
                                    📊 <strong>Historical Data</strong> - Observed data for{" "}
                                    {selectedDate}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Error Display */}
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
                        <strong>Error:</strong> {error}
                    </div>
                )}



                {/* Visual Map */}
                {selectedDate && mapPoints.length > 0 && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                            🗺️ Field Map Visualization
                        </h2>
                        <div className="flex gap-4 mb-4">
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 rounded-full bg-red-500"></div>
                                <span className="text-sm">High Risk</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
                                <span className="text-sm">Medium Risk</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 rounded-full bg-green-500"></div>
                                <span className="text-sm">Low Risk</span>
                            </div>
                        </div>
                        <LeafletMap points={mapPoints} onPointClick={handleLocationClick} />
                        <div className="mt-4 text-sm text-gray-600 text-center">
                            Click on any point to view detailed information and time series data
                        </div>
                    </div>
                )}

                {/* Date Summary Timeline */}
                {dateSummaries.length > 0 && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                            📈 Date Summary Timeline
                        </h2>
                        <div className="overflow-x-auto">
                            <div className="flex gap-2 pb-4">
                                {dateSummaries.map((summary) => {
                                    const isCurrent = summary.date === selectedDate;
                                    const isObserved = summary.date <= lastObservedDate;
                                    return (
                                        <button
                                            key={summary.date}
                                            onClick={() => setSelectedDate(summary.date)}
                                            className={`shrink-0 p-3 rounded-lg border-2 transition ${isCurrent
                                                ? "border-blue-500 bg-blue-50"
                                                : "border-gray-300 bg-white hover:border-blue-300"
                                                }`}
                                            style={{ minWidth: "120px" }}
                                        >
                                            <div className="text-xs font-medium text-gray-600">
                                                {summary.date}
                                            </div>
                                            <div className="text-lg font-bold text-gray-900">
                                                {summary.avg_pred.toFixed(1)}%
                                            </div>
                                            <div className="text-xs text-gray-600">
                                                {summary.risk_count} risks
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {summary.point_count} pts
                                            </div>
                                            {!isObserved && (
                                                <div className="text-xs text-purple-600 font-semibold">
                                                    FUTURE
                                                </div>
                                            )}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* Map Data Table */}
                {mapPoints.length > 0 && (
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                            🗺️ Location Map Data
                        </h2>
                        <div className="text-sm text-gray-600 mb-4">
                            Showing {mapPoints.length} locations
                            {drynessThreshold && ` (filtered by threshold ≤ ${drynessThreshold}%)`}
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Location
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Soil Humidity
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Predicted
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Risk
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Action
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Recommend (m³/mu)
                                        </th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                            Details
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {mapPoints.slice(0, 100).map((point, idx) => (
                                        <tr
                                            key={idx}
                                            className="hover:bg-gray-50 cursor-pointer transition"
                                        >
                                            <td className="px-4 py-3 whitespace-nowrap text-sm font-mono">
                                                ({point.loc_x.toFixed(4)}, {point.loc_y.toFixed(4)})
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                                                {point.soil_humidity.toFixed(1)}%
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold">
                                                {point.pred_humidity
                                                    ? `${point.pred_humidity.toFixed(1)}%`
                                                    : "N/A"}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <span
                                                    className={`px-2 py-1 text-xs rounded-full ${getRiskColor(
                                                        point.risk_level
                                                    )}`}
                                                >
                                                    {point.risk_level.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                                                {point.action === "IRRIGATE" ? (
                                                    <span className="text-blue-600 font-semibold">
                                                        💧 IRRIGATE
                                                    </span>
                                                ) : (
                                                    <span className="text-gray-500">✓ SKIP</span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap text-sm font-bold text-blue-600">
                                                {point.recommended_irrigation.toFixed(2)}
                                            </td>
                                            <td className="px-4 py-3 whitespace-nowrap">
                                                <button
                                                    onClick={() => handleLocationClick(point)}
                                                    className="text-blue-600 hover:text-blue-800 text-sm"
                                                >
                                                    View →
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {mapPoints.length > 100 && (
                            <div className="mt-4 text-center text-sm text-gray-600">
                                Showing first 100 of {mapPoints.length} locations
                            </div>
                        )}
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="text-center py-12">
                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        <p className="mt-4 text-gray-600">Loading data...</p>
                    </div>
                )}

                {/* Empty State */}
                {!loading && mapPoints.length === 0 && selectedDate && (
                    <div className="text-center py-12 bg-white rounded-lg shadow-md">
                        <p className="text-gray-600 text-lg">
                            No data available for {selectedDate}
                        </p>
                        <button
                            onClick={generatePredictions}
                            className="mt-4 bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700"
                        >
                            Generate Predictions
                        </button>
                    </div>
                )}

                {/* Location Detail Modal with Time Series */}
                {selectedLocation && (
                    <div className="fixed inset-0 bg-opacity-50 flex items-center justify-center z-9999 overflow-y-auto p-4">
                        <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
                            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-start">
                                <h3 className="text-xl font-bold text-gray-900">
                                    Location Details & Time Series
                                </h3>
                                <button
                                    onClick={() => {
                                        setSelectedLocation(null);
                                        setTimeSeriesData(null);
                                    }}
                                    className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
                                >
                                    ✕
                                </button>
                            </div>

                            <div className="p-6">
                                {/* Location Info */}
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                                    <div className="bg-gray-50 p-4 rounded-lg">
                                        <div className="text-sm text-gray-500">Coordinates</div>
                                        <div className="font-mono font-semibold text-sm">
                                            X: {selectedLocation.loc_x.toFixed(4)}, Y:{" "}
                                            {selectedLocation.loc_y.toFixed(4)}
                                        </div>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded-lg">
                                        <div className="text-sm text-gray-500">Current Humidity</div>
                                        <div className="text-2xl font-bold text-blue-600">
                                            {selectedLocation.soil_humidity.toFixed(1)}%
                                        </div>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded-lg">
                                        <div className="text-sm text-gray-500">
                                            Predicted Humidity
                                        </div>
                                        <div className="text-2xl font-bold text-green-600">
                                            {selectedLocation.pred_humidity
                                                ? `${selectedLocation.pred_humidity.toFixed(1)}%`
                                                : "N/A"}
                                        </div>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded-lg">
                                        <div className="text-sm text-gray-500">Risk Level</div>
                                        <span
                                            className={`inline-block px-3 py-1 rounded-full font-semibold text-sm ${getRiskColor(
                                                selectedLocation.risk_level
                                            )}`}
                                        >
                                            {selectedLocation.risk_level.toUpperCase()}
                                        </span>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded-lg">
                                        <div className="text-sm text-gray-500">
                                            Recommended Irrigation
                                        </div>
                                        <div className="text-2xl font-bold text-purple-600">
                                            {selectedLocation.recommended_irrigation.toFixed(2)} m³/mu
                                        </div>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded-lg">
                                        <div className="text-sm text-gray-500">
                                            Days Since Irrigation
                                        </div>
                                        <div className="text-2xl font-bold">
                                            {selectedLocation.days_since_irrigation}
                                        </div>
                                    </div>
                                </div>

                                {/* Additional Info */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                    <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                                        <div className="text-xs text-gray-600">Soil Temp</div>
                                        <div className="text-lg font-semibold text-blue-700">
                                            {selectedLocation.soil_temp.toFixed(1)}°C
                                        </div>
                                    </div>
                                    <div className="bg-orange-50 p-3 rounded-lg border border-orange-200">
                                        <div className="text-xs text-gray-600">Air Temp</div>
                                        <div className="text-lg font-semibold text-orange-700">
                                            {selectedLocation.air_temp.toFixed(1)}°C
                                        </div>
                                    </div>
                                    <div className="bg-cyan-50 p-3 rounded-lg border border-cyan-200">
                                        <div className="text-xs text-gray-600">Rain</div>
                                        <div className="text-lg font-semibold text-cyan-700">
                                            {selectedLocation.rain.toFixed(1)} mm
                                        </div>
                                    </div>
                                    <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                                        <div className="text-xs text-gray-600">Action</div>
                                        <div className="text-lg font-semibold text-purple-700">
                                            {selectedLocation.action}
                                        </div>
                                    </div>
                                </div>

                                {/* Time Series Chart */}
                                {timeSeriesData && (
                                    <div className="border-t pt-6">
                                        <h4 className="text-lg font-semibold mb-4">
                                            📊 Time Series History & Predictions
                                        </h4>
                                        <div className="bg-gray-50 p-4 rounded-lg mb-4">
                                            <ResponsiveContainer width="100%" height={400}>
                                                <LineChart
                                                    data={(() => {
                                                        const lastObserved = timeSeriesData.last_observed_date;
                                                        return timeSeriesData.dates.map(
                                                            (date: string, idx: number) => {
                                                                const isFuture = lastObserved && date > lastObserved;
                                                                return {
                                                                    date,
                                                                    actual: timeSeriesData.actual[idx],
                                                                    predicted: timeSeriesData.pred[idx],
                                                                    // For future dates, use prediction as the main value
                                                                    futurePrediction: isFuture ? timeSeriesData.pred[idx] : null,
                                                                    irrigation: timeSeriesData.irrigation[idx],
                                                                };
                                                            }
                                                        );
                                                    })()}
                                                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                                >
                                                    <CartesianGrid strokeDasharray="3 3" />
                                                    <XAxis
                                                        dataKey="date"
                                                        angle={-45}
                                                        textAnchor="end"
                                                        height={80}
                                                        tick={{ fontSize: 12 }}
                                                    />
                                                    <YAxis
                                                        yAxisId="left"
                                                        label={{
                                                            value: "Humidity (%)",
                                                            angle: -90,
                                                            position: "insideLeft",
                                                        }}
                                                    />
                                                    <YAxis
                                                        yAxisId="right"
                                                        orientation="right"
                                                        label={{
                                                            value: "Irrigation (m³/mu)",
                                                            angle: 90,
                                                            position: "insideRight",
                                                        }}
                                                    />
                                                    <Tooltip
                                                        contentStyle={{
                                                            backgroundColor: "rgba(255, 255, 255, 0.95)",
                                                            border: "1px solid #ccc",
                                                            borderRadius: "8px",
                                                        }}
                                                    />
                                                    <Legend />
                                                    <Line
                                                        yAxisId="left"
                                                        type="monotone"
                                                        dataKey="actual"
                                                        stroke="#3b82f6"
                                                        strokeWidth={2}
                                                        name="Actual Humidity"
                                                        dot={{ r: 4 }}
                                                        connectNulls
                                                    />
                                                    <Line
                                                        yAxisId="left"
                                                        type="monotone"
                                                        dataKey="predicted"
                                                        stroke="#22c55e"
                                                        strokeWidth={2}
                                                        name="Predicted Humidity (Historical)"
                                                        strokeDasharray="5 5"
                                                        dot={{ r: 4 }}
                                                        connectNulls
                                                    />
                                                    <Line
                                                        yAxisId="left"
                                                        type="monotone"
                                                        dataKey="futurePrediction"
                                                        stroke="#a855f7"
                                                        strokeWidth={3}
                                                        name="AI Future Prediction"
                                                        strokeDasharray="8 8"
                                                        dot={{ r: 5, fill: "#a855f7" }}
                                                        connectNulls
                                                    />
                                                    <Line
                                                        yAxisId="right"
                                                        type="stepAfter"
                                                        dataKey="irrigation"
                                                        stroke="#0891b2"
                                                        strokeWidth={2}
                                                        name="Irrigation Applied"
                                                        dot={{ r: 3 }}
                                                    />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        </div>
                                        {timeSeriesData.last_observed_date && (
                                            <div className="text-sm text-gray-600 text-center">
                                                📅 Last observed date:{" "}
                                                <span className="font-semibold">
                                                    {timeSeriesData.last_observed_date}
                                                </span>
                                                {" "} | Dates after this show AI predictions in purple
                                            </div>
                                        )}
                                    </div>
                                )}

                                {!timeSeriesData && (
                                    <div className="text-center py-8">
                                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                        <p className="mt-2 text-gray-600">Loading time series data...</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
