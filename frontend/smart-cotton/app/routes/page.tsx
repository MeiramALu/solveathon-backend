'use client'

import dynamic from 'next/dynamic'
import { useState } from 'react'
import { Truck, Plus, Trash2, Play, Loader2, Sparkles, MapPin } from 'lucide-react'

// Dynamically import the map component (disable SSR)
const RouteOptimizationMap = dynamic(
    () => import('@/components/maps/route-optimization-map'),
    {
        ssr: false,
        loading: () => (
            <div className="h-full w-full bg-slate-100 flex items-center justify-center animate-pulse">
                <span className="text-slate-400 font-medium">Loading Map...</span>
            </div>
        )
    }
)

interface Field {
    id: number
    lat: number
    lon: number
    demand: number
    serviceTimeMinutes: number
}

interface Vehicle {
    id: number
    name: string
    capacity: number
    shiftMinutes: number
    color: string
}

interface Depot {
    lat: number
    lon: number
}

interface OrsRoute {
    distance?: number
    duration?: number
    geometry?: string | { coordinates: number[][] }
    steps?: unknown[]
}

interface OrsSolution {
    routes?: OrsRoute[]
}

const VEHICLE_COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899']

export default function RoutesPage() {
    const [depot, setDepot] = useState<Depot>({ lat: 43.2973, lon: 68.2517 })

    const [fields, setFields] = useState<Field[]>([])
    const [nextFieldId, setNextFieldId] = useState(1)

    // Field defaults
    const [defaultDemand, setDefaultDemand] = useState(5)
    const [defaultServiceTime, setDefaultServiceTime] = useState(15)
    const [numFieldsToAdd, setNumFieldsToAdd] = useState(1)

    const [vehicles, setVehicles] = useState<Vehicle[]>([
        { id: 1, name: 'Harvester 1', capacity: 20, shiftMinutes: 480, color: VEHICLE_COLORS[0] }
    ])
    const [nextVehicleId, setNextVehicleId] = useState(2)

    const [routes, setRoutes] = useState<OrsSolution | null>(null)
    const [optimizing, setOptimizing] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [aiSummary, setAiSummary] = useState<string | null>(null)
    const [generatingAI, setGeneratingAI] = useState(false)

    // Assumptions
    const [avgSpeed, setAvgSpeed] = useState(40)

    // Add field by clicking on map
    const handleMapClick = (lat: number, lon: number) => {
        const newField: Field = {
            id: nextFieldId,
            lat,
            lon,
            demand: defaultDemand,
            serviceTimeMinutes: defaultServiceTime
        }
        setFields([...fields, newField])
        setNextFieldId(nextFieldId + 1)
    }

    // Add multiple fields at random nearby locations
    const addMultipleFields = () => {
        const newFields: Field[] = []
        for (let i = 0; i < numFieldsToAdd; i++) {
            // Random offset within ~5km (roughly 0.045 degrees)
            const latOffset = (Math.random() - 0.5) * 0.09
            const lonOffset = (Math.random() - 0.5) * 0.09

            newFields.push({
                id: nextFieldId + i,
                lat: depot.lat + latOffset,
                lon: depot.lon + lonOffset,
                demand: defaultDemand,
                serviceTimeMinutes: defaultServiceTime
            })
        }
        setFields([...fields, ...newFields])
        setNextFieldId(nextFieldId + numFieldsToAdd)
    }

    // Remove field
    const removeField = (id: number) => {
        setFields(fields.filter(f => f.id !== id))
    }

    // Update field
    const updateField = (id: number, updates: Partial<Field>) => {
        setFields(fields.map(f => f.id === id ? { ...f, ...updates } : f))
    }

    // Add vehicle
    const addVehicle = () => {
        const newVehicle: Vehicle = {
            id: nextVehicleId,
            name: `Vehicle ${nextVehicleId}`,
            capacity: 20,
            shiftMinutes: 480,
            color: VEHICLE_COLORS[(nextVehicleId - 1) % VEHICLE_COLORS.length]
        }
        setVehicles([...vehicles, newVehicle])
        setNextVehicleId(nextVehicleId + 1)
    }

    // Remove vehicle
    const removeVehicle = (id: number) => {
        setVehicles(vehicles.filter(v => v.id !== id))
    }

    // Update vehicle
    const updateVehicle = (id: number, updates: Partial<Vehicle>) => {
        setVehicles(vehicles.map(v => v.id === id ? { ...v, ...updates } : v))
    }



    // Optimize routes
    const handleOptimize = async () => {
        if (fields.length === 0) {
            setError('Please add at least one field by clicking on the map')
            return
        }

        if (vehicles.length === 0) {
            setError('Please add at least one vehicle')
            return
        }

        setOptimizing(true)
        setError(null)
        setAiSummary(null)

        try {
            const response = await fetch('/api/logistics/optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    depot,
                    fields,
                    vehicles
                })
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.error || 'Optimization failed')
            }

            setRoutes(data.orsSolution)

            // Generate AI summary
            if (data.orsSolution && data.orsSolution.routes) {
                generateAISummary(data.orsSolution)
            }
        } catch (err) {
            console.error('Optimization error:', err)
            setError(err instanceof Error ? err.message : 'Failed to optimize routes')
        } finally {
            setOptimizing(false)
        }
    }

    // Generate AI summary
    const generateAISummary = async (orsSolution: { routes?: Array<{ distance?: number; duration?: number }> }) => {
        setGeneratingAI(true)
        try {
            const totalDistance = orsSolution.routes?.reduce((sum, r) => sum + (r.distance || 0), 0) || 0
            const totalDuration = orsSolution.routes?.reduce((sum, r) => sum + (r.duration || 0), 0) || 0
            const totalCapacity = vehicles.reduce((sum, v) => sum + v.capacity, 0)

            const facts = {
                totals: {
                    distance: (totalDistance / 1000).toFixed(1),
                    time: (totalDuration / 60).toFixed(0),
                    capacity: totalCapacity
                },
                vehicles: vehicles.map((v, idx) => {
                    const route = orsSolution.routes?.[idx]
                    return {
                        name: v.name,
                        distance: ((route?.distance || 0) / 1000).toFixed(1),
                        hours: ((route?.duration || 0) / 3600).toFixed(1),
                        load: v.capacity
                    }
                }),
                unassignedCount: 0
            }

            const response = await fetch('/api/logistics/ai-summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ facts })
            })

            const data = await response.json()
            if (response.ok) {
                setAiSummary(data.text)
            }
        } catch (err) {
            console.error('AI summary error:', err)
        } finally {
            setGeneratingAI(false)
        }
    }

    return (
        <div className="relative w-full h-screen bg-slate-50 flex">
            {/* Sidebar */}
            <div className="w-96 bg-white border-r border-slate-200 overflow-y-auto">
                <div className="p-6">
                    {/* Header */}
                    <div className="mb-6">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="bg-orange-100 p-2 rounded-lg">
                                <Truck className="w-6 h-6 text-orange-600" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold text-slate-800">Route Optimization</h1>
                                <p className="text-xs text-slate-700">Cotton Harvest Logistics</p>
                            </div>
                        </div>
                    </div>

                    {/* Depot */}
                    <div className="mb-6">
                        <h2 className="text-sm font-semibold text-slate-700 mb-3">🏭 Depot Location</h2>
                        <div className="bg-slate-50 rounded-lg p-3 text-sm">
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="text-xs text-slate-700 font-medium">Latitude</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        value={depot.lat}
                                        onChange={(e) => setDepot({ ...depot, lat: parseFloat(e.target.value) })}
                                        className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-700 font-medium">Longitude</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        value={depot.lon}
                                        onChange={(e) => setDepot({ ...depot, lon: parseFloat(e.target.value) })}
                                        className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                                    />
                                </div>
                            </div>
                            <p className="text-xs text-slate-700 mt-2">Drag the depot marker on the map</p>
                        </div>
                    </div>

                    {/* Fields */}
                    <div className="mb-6">
                        <h2 className="text-sm font-semibold text-slate-700 mb-3">🌾 Cotton Fields ({fields.length})</h2>

                        {/* Field Defaults & Bulk Add */}
                        <div className="bg-slate-50 rounded-lg p-3 mb-3 border border-slate-200">
                            <p className="text-xs text-slate-700 font-medium mb-2">Default Field Settings</p>
                            <div className="grid grid-cols-3 gap-2 mb-2">
                                <div>
                                    <label className="text-xs text-slate-700 font-medium">Yield (tons)</label>
                                    <input
                                        type="number"
                                        value={defaultDemand}
                                        onChange={(e) => setDefaultDemand(parseFloat(e.target.value))}
                                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-700 font-medium">Service (min)</label>
                                    <input
                                        type="number"
                                        value={defaultServiceTime}
                                        onChange={(e) => setDefaultServiceTime(parseFloat(e.target.value))}
                                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs"
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-700 font-medium">Count</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="20"
                                        value={numFieldsToAdd}
                                        onChange={(e) => setNumFieldsToAdd(parseInt(e.target.value))}
                                        className="w-full px-2 py-1 border border-slate-300 rounded text-xs"
                                    />
                                </div>
                            </div>
                            <button
                                onClick={addMultipleFields}
                                className="w-full flex items-center justify-center gap-1 px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
                            >
                                <MapPin className="w-3 h-3" />
                                Add {numFieldsToAdd} Random Field{numFieldsToAdd > 1 ? 's' : ''}
                            </button>
                            <p className="text-xs text-slate-700 mt-2">Or click map to add individual fields</p>
                        </div>

                        {fields.length === 0 && (
                            <p className="text-sm text-slate-700 mb-3">No fields yet</p>
                        )}
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {fields.map((field) => (
                                <div key={field.id} className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm font-semibold text-slate-700">Field #{field.id}</span>
                                        <button
                                            onClick={() => removeField(field.id)}
                                            className="text-red-500 hover:text-red-700"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div>
                                            <label className="text-xs text-slate-700 font-medium">Yield (tons)</label>
                                            <input
                                                type="number"
                                                value={field.demand}
                                                onChange={(e) => updateField(field.id, { demand: parseFloat(e.target.value) })}
                                                className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-700 font-medium">Service (min)</label>
                                            <input
                                                type="number"
                                                value={field.serviceTimeMinutes}
                                                onChange={(e) => updateField(field.id, { serviceTimeMinutes: parseFloat(e.target.value) })}
                                                className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Vehicles */}
                    <div className="mb-6">
                        <div className="flex items-center justify-between mb-3">
                            <h2 className="text-sm font-semibold text-slate-700">🚛 Vehicles ({vehicles.length})</h2>
                            <button
                                onClick={addVehicle}
                                className="flex items-center gap-1 px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
                            >
                                <Plus className="w-3 h-3" />
                                Add
                            </button>
                        </div>
                        <div className="space-y-2">
                            {vehicles.map((vehicle) => (
                                <div key={vehicle.id} className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            <div
                                                className="w-3 h-3 rounded-full"
                                                style={{ backgroundColor: vehicle.color }}
                                            />
                                            <input
                                                type="text"
                                                value={vehicle.name}
                                                onChange={(e) => updateVehicle(vehicle.id, { name: e.target.value })}
                                                className="text-sm font-semibold text-slate-700 bg-transparent border-none focus:outline-none"
                                            />
                                        </div>
                                        <button
                                            onClick={() => removeVehicle(vehicle.id)}
                                            className="text-red-500 hover:text-red-700"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <div>
                                            <label className="text-xs text-slate-700 font-medium">Capacity (tons)</label>
                                            <input
                                                type="number"
                                                value={vehicle.capacity}
                                                onChange={(e) => updateVehicle(vehicle.id, { capacity: parseFloat(e.target.value) })}
                                                className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-700 font-medium">Shift (min)</label>
                                            <input
                                                type="number"
                                                value={vehicle.shiftMinutes}
                                                onChange={(e) => updateVehicle(vehicle.id, { shiftMinutes: parseFloat(e.target.value) })}
                                                className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Assumptions */}
                    <div className="mb-6">
                        <h2 className="text-sm font-semibold text-slate-700 mb-3">⚙️ Assumptions</h2>
                        <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                            <label className="text-xs text-slate-700 font-medium">Average Speed (km/h)</label>
                            <input
                                type="number"
                                min="1"
                                value={avgSpeed}
                                onChange={(e) => setAvgSpeed(parseFloat(e.target.value))}
                                className="w-full px-2 py-1 border border-slate-300 rounded text-sm"
                            />
                            <p className="text-xs text-slate-700 mt-2">Used for baseline comparison calculations</p>
                        </div>
                    </div>

                    {/* Optimize Button */}
                    <button
                        onClick={handleOptimize}
                        disabled={optimizing || fields.length === 0 || vehicles.length === 0}
                        className="w-full py-3 bg-orange-500 text-white rounded-lg font-semibold hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {optimizing ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Optimizing...
                            </>
                        ) : (
                            <>
                                <Play className="w-5 h-5" />
                                Optimize Routes
                            </>
                        )}
                    </button>

                    {/* Error Message */}
                    {error && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                            {error}
                        </div>
                    )}

                    {/* AI Summary */}
                    {(aiSummary || generatingAI) && (
                        <div className="mt-4 p-4 bg-linear-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                                <Sparkles className="w-4 h-4 text-purple-600" />
                                <h3 className="text-sm font-semibold text-purple-900">AI Insights</h3>
                            </div>
                            {generatingAI ? (
                                <div className="flex items-center gap-2 text-sm text-purple-700">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Generating insights...
                                </div>
                            ) : (
                                <div className="text-sm text-purple-800 whitespace-pre-line">{aiSummary}</div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Map Container */}
            <div className="flex-1 relative">
                <RouteOptimizationMap
                    depot={depot}
                    fields={fields}
                    vehicles={vehicles}
                    routes={routes}
                    onDepotMove={(newDepot) => setDepot(newDepot)}
                    onMapClick={handleMapClick}
                />
            </div>
        </div>
    )
}
