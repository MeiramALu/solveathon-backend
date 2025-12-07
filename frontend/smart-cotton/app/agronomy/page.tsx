'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { Sprout, MapPin, Loader2, TrendingUp, ThermometerSun } from 'lucide-react'

const AgronomyMap = dynamic(() => import('@/components/agronomy/agronomy-map'), {
    ssr: false,
    loading: () => <div className="w-full h-[400px] bg-slate-100 rounded-lg animate-pulse" />
})

type SeedRecommendation = {
    variety: string
    predicted_yield: number
    origin: string
}

type WeatherData = {
    temp?: number
    rain_summer?: number
    humidity?: number
    soil_ph?: number
}

type AgronomyData = {
    location_info: string
    recommendations: SeedRecommendation[]
    weather?: WeatherData
    latitude?: number
    longitude?: number
}

export default function AgronomyPage() {
    const [loading, setLoading] = useState(false)
    const [data, setData] = useState<AgronomyData | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [mapCoords, setMapCoords] = useState<{ lat: number; lon: number } | null>(null)

    // Auto-fetch on mount
    useEffect(() => {
        fetchAgronomyData()
    }, [])

    const fetchAgronomyData = async (lat?: string, lon?: string) => {
        setLoading(true)
        setError(null)

        try {
            const url = lat && lon
                ? `${process.env.NEXT_PUBLIC_API_URL}/api/agronomy_predict/?lat=${lat}&lon=${lon}`
                : `${process.env.NEXT_PUBLIC_API_URL}/api/agronomy_predict/`

            const response = await fetch(url)

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const result = await response.json()
            setData(result)

            // Set map coordinates from API or input
            if (lat && lon) {
                setMapCoords({ lat: parseFloat(lat), lon: parseFloat(lon) })
            } else if (result.latitude && result.longitude) {
                setMapCoords({ lat: result.latitude, lon: result.longitude })
            } else {
                // Default to Kazakhstan center if no coords available
                setMapCoords({ lat: 48.0196, lon: 66.9237 })
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch agronomy data')
        } finally {
            setLoading(false)
        }
    }

    const getRankIcon = (index: number) => {
        if (index === 0) return '🏆'
        if (index === 1) return '🥈'
        if (index === 2) return '🥉'
        return '🌱'
    }

    return (
        <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 p-6">
            <div className="max-w-7xl mx-auto pb-6">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-slate-800 flex items-center gap-3">
                        <Sprout className="w-10 h-10 text-green-600" />
                        Smart Agronomy Recommendations
                    </h1>
                    <p className="text-slate-600 mt-2">AI-powered seed recommendations based on your location and climate</p>
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                        <p className="text-red-800 font-medium">⚠️ {error}</p>
                    </div>
                )}

                {/* Loading */}
                {loading && (
                    <div className="flex flex-col items-center justify-center py-20">
                        <Loader2 className="w-12 h-12 animate-spin text-green-600 mb-4" />
                        <p className="text-slate-600">Analyzing location and climate data...</p>
                    </div>
                )}

                {/* Results */}
                {data && !loading && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Map & Location Info */}
                        <div className="lg:col-span-3 bg-white rounded-xl shadow-lg p-6">
                            <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                                <MapPin className="w-6 h-6 text-green-600" />
                                Location Information
                            </h2>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Map */}
                                <div className="h-[400px] rounded-lg overflow-hidden border border-slate-200 shadow-md">
                                    {mapCoords && (
                                        <AgronomyMap
                                            latitude={mapCoords.lat}
                                            longitude={mapCoords.lon}
                                            region={data.location_info}
                                        />
                                    )}
                                </div>

                                {/* Location Details */}
                                <div className="flex flex-col justify-center space-y-4">
                                    <div className="p-6 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg text-center border border-green-200">
                                        <p className="text-3xl font-bold text-green-700">{data.location_info}</p>
                                        <p className="text-sm text-slate-600 mt-2">Your region</p>
                                    </div>

                                    {mapCoords && (
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                                                <p className="text-sm text-blue-600 font-medium mb-1">Latitude</p>
                                                <p className="text-lg font-bold text-slate-800">{mapCoords.lat.toFixed(4)}°N</p>
                                            </div>
                                            <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                                                <p className="text-sm text-purple-600 font-medium mb-1">Longitude</p>
                                                <p className="text-lg font-bold text-slate-800">{mapCoords.lon.toFixed(4)}°E</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Weather & Soil Conditions */}
                        {data.weather && (
                            <div className="lg:col-span-3 bg-white rounded-xl shadow-lg p-6">
                                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                                    <ThermometerSun className="w-6 h-6 text-orange-600" />
                                    Climate & Soil Data
                                </h2>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {data.weather.temp !== undefined && (
                                        <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
                                            <p className="text-sm text-orange-600 font-medium mb-1">Temperature</p>
                                            <p className="text-2xl font-bold text-slate-800">{data.weather.temp}°C</p>
                                        </div>
                                    )}
                                    {data.weather.rain_summer !== undefined && (
                                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                                            <p className="text-sm text-blue-600 font-medium mb-1">Summer Rain</p>
                                            <p className="text-2xl font-bold text-slate-800">{data.weather.rain_summer} mm</p>
                                        </div>
                                    )}
                                    {data.weather.humidity !== undefined && (
                                        <div className="p-4 bg-cyan-50 rounded-lg border border-cyan-100">
                                            <p className="text-sm text-cyan-600 font-medium mb-1">Humidity</p>
                                            <p className="text-2xl font-bold text-slate-800">{data.weather.humidity}%</p>
                                        </div>
                                    )}
                                    {data.weather.soil_ph !== undefined && (
                                        <div className="p-4 bg-amber-50 rounded-lg border border-amber-100">
                                            <p className="text-sm text-amber-600 font-medium mb-1">Soil pH</p>
                                            <p className="text-2xl font-bold text-slate-800">{data.weather.soil_ph}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Seed Recommendations */}
                        <div className="lg:col-span-3 bg-white rounded-xl shadow-lg p-6">
                            <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                                <TrendingUp className="w-7 h-7 text-green-600" />
                                Top Seed Recommendations
                            </h2>

                            {data.recommendations && data.recommendations.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {data.recommendations.map((seed, idx) => (
                                        <div
                                            key={idx}
                                            className={`relative p-6 rounded-xl border-2 transition-all hover:shadow-xl hover:-translate-y-1 ${idx === 0
                                                ? 'bg-gradient-to-br from-yellow-50 to-amber-50 border-yellow-400'
                                                : idx === 1
                                                    ? 'bg-gradient-to-br from-slate-50 to-gray-50 border-slate-400'
                                                    : 'bg-gradient-to-br from-orange-50 to-red-50 border-orange-400'
                                                }`}
                                        >
                                            <div className="absolute -top-4 -right-4 text-5xl">
                                                {getRankIcon(idx)}
                                            </div>

                                            <div className="mb-4">
                                                <h3 className="text-xl font-bold text-slate-800 mb-2">
                                                    {seed.variety}
                                                </h3>
                                                <p className="text-sm text-slate-600 italic">
                                                    Origin: {seed.origin}
                                                </p>
                                            </div>

                                            <div className="space-y-3">
                                                <div className="p-4 bg-white rounded-lg border border-slate-200">
                                                    <p className="text-sm text-slate-600 mb-1">Predicted Yield</p>
                                                    <p className="text-2xl font-bold text-green-700">
                                                        {seed.predicted_yield.toFixed(1)} ц/га
                                                    </p>
                                                </div>

                                                <div className={`px-4 py-2 rounded-lg text-center font-semibold ${idx === 0
                                                    ? 'bg-yellow-400 text-yellow-900'
                                                    : idx === 1
                                                        ? 'bg-slate-300 text-slate-800'
                                                        : 'bg-orange-400 text-orange-900'
                                                    }`}>
                                                    {idx === 0 ? 'Best Choice' : idx === 1 ? 'Good Alternative' : 'Also Recommended'}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-slate-500">
                                    <Sprout className="w-16 h-16 mx-auto mb-4 opacity-30" />
                                    <p>No seed recommendations available for this location</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
