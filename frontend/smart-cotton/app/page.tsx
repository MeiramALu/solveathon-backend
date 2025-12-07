'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import AnalysisPanel from '@/components/water/analysis-panel'
import { getSmartIrrigationPlan, SmartPlan } from '@/service/water-service'

// Dynamic Map import
const Map = dynamic(() => import('@/components/maps/map'), {
  ssr: false,
  loading: () => <div className="h-full w-full bg-slate-200 animate-pulse">Loading Map...</div>
})

export default function WaterPage() {
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState<SmartPlan | null>(null)

  // Handler for map clicks
  const handleMapClick = async (lat: number, lon: number) => {
    setLoading(true)
    try {
      // Call our TS service
      const result = await getSmartIrrigationPlan(lat, lon)
      setPlan(result)
    } catch (error) {
      console.error("Failed to fetch plan", error)
    } finally {
      setLoading(false)
    }
  }

  // Determine marker color based on result
  const markers = plan ? [{
    lat: plan.location.lat,
    lon: plan.location.lon,
    color: plan.drought.level === 'high' ? '#ef4444' : plan.drought.level === 'medium' ? '#eab308' : '#22c55e'
  }] : []

  return (
    <section className="h-full w-full relative rounded-xl overflow-hidden shadow-xl border border-slate-200 bg-white">

      {/* 1. The Map (Interactive) */}
      <Map
        activeModule="water"
        onMapClick={handleMapClick}
        markers={markers}
      />

      {/* 2. The Analysis Panel (Overlaid) */}
      <AnalysisPanel plan={plan} loading={loading} />

    </section>
  )
}