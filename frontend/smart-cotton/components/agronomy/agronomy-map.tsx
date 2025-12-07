'use client'

import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

type AgronomyMapProps = {
    latitude: number
    longitude: number
    region: string
}

export default function AgronomyMap({ latitude, longitude, region }: AgronomyMapProps) {
    const mapRef = useRef<L.Map | null>(null)
    const mapContainerRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (!mapContainerRef.current) return

        // Initialize map if not already initialized
        if (!mapRef.current) {
            mapRef.current = L.map(mapContainerRef.current).setView([latitude, longitude], 10)

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                maxZoom: 19
            }).addTo(mapRef.current)
        }

        // Clear existing markers
        mapRef.current.eachLayer((layer) => {
            if (layer instanceof L.Marker) {
                mapRef.current?.removeLayer(layer)
            }
        })

        // Create custom icon
        const customIcon = L.divIcon({
            html: `
                <div style="
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    width: 40px;
                    height: 40px;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    border: 3px solid white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <div style="
                        transform: rotate(45deg);
                        font-size: 20px;
                    ">🌾</div>
                </div>
            `,
            className: 'custom-marker',
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        })

        // Add marker
        L.marker([latitude, longitude], { icon: customIcon })
            .addTo(mapRef.current)
            .bindPopup(`
                <div style="text-align: center; padding: 8px;">
                    <strong style="font-size: 16px; color: #059669;">${region}</strong><br/>
                    <span style="color: #64748b; font-size: 12px;">
                        ${latitude.toFixed(4)}°N, ${longitude.toFixed(4)}°E
                    </span>
                </div>
            `)
            .openPopup()

        // Update map view
        mapRef.current.setView([latitude, longitude], 10, { animate: true })

        return () => {
            // Cleanup on unmount
            if (mapRef.current) {
                mapRef.current.remove()
                mapRef.current = null
            }
        }
    }, [latitude, longitude, region])

    return (
        <div
            ref={mapContainerRef}
            className="w-full h-full rounded-lg"
            style={{ minHeight: '400px' }}
        />
    )
}
