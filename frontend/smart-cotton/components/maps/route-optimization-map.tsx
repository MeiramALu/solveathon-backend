'use client'

import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix Leaflet icon issue with Next.js
if (typeof window !== 'undefined') {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (L.Icon.Default.prototype as any)._getIconUrl
    L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    })
}

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

interface RouteOptimizationMapProps {
    depot: Depot
    fields: Field[]
    vehicles: Vehicle[]
    routes: OrsSolution | null
    onDepotMove: (depot: Depot) => void
    onMapClick: (lat: number, lon: number) => void
}

export default function RouteOptimizationMap({
    depot,
    fields,
    vehicles,
    routes,
    onDepotMove,
    onMapClick
}: RouteOptimizationMapProps) {
    const mapRef = useRef<L.Map | null>(null)
    const depotMarkerRef = useRef<L.Marker | null>(null)
    const fieldMarkersRef = useRef<L.Layer[]>([])
    const routeLayersRef = useRef<L.Polyline[]>([])

    // Initialize map
    useEffect(() => {
        if (!mapRef.current) {
            const map = L.map('route-optimization-map').setView([depot.lat, depot.lon], 11)

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map)

            // Add depot marker
            const depotIcon = L.divIcon({
                className: '',
                html: `
                    <div style="
                        background: #ef4444;
                        width: 36px;
                        height: 36px;
                        border-radius: 50%;
                        border: 4px solid white;
                        box-shadow: 0 3px 10px rgba(0,0,0,0.4);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 18px;
                        cursor: move;
                        position: relative;
                    ">
                        🏭
                    </div>
                `,
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            })

            const depotMarker = L.marker([depot.lat, depot.lon], {
                icon: depotIcon,
                draggable: true
            }).addTo(map)

            depotMarker.bindPopup('Depot / Cotton Gin')

            depotMarker.on('dragend', () => {
                const { lat, lng } = depotMarker.getLatLng()
                onDepotMove({ lat, lon: lng })
            })

            depotMarkerRef.current = depotMarker

            // Add map click handler
            map.on('click', (e: L.LeafletMouseEvent) => {
                onMapClick(e.latlng.lat, e.latlng.lng)
            })

            mapRef.current = map
        }

        return () => {
            if (mapRef.current) {
                mapRef.current.remove()
                mapRef.current = null
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    // Update depot marker position
    useEffect(() => {
        if (depotMarkerRef.current) {
            depotMarkerRef.current.setLatLng([depot.lat, depot.lon])
        }
    }, [depot])

    // Update field markers
    useEffect(() => {
        if (!mapRef.current) return

        // Remove old markers
        fieldMarkersRef.current.forEach(marker => marker.remove())
        fieldMarkersRef.current = []

        // Add new markers - use circleMarkers to not block map clicks
        fields.forEach(field => {
            const marker = L.circleMarker([field.lat, field.lon], {
                radius: 8,
                color: '#1e40af',
                fillColor: '#3b82f6',
                fillOpacity: 0.9,
                weight: 2
            }).addTo(mapRef.current!)

            // Add number label
            const labelIcon = L.divIcon({
                className: '',
                html: `<div style="
                    background: rgba(59, 130, 246, 0.95);
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 11px;
                    white-space: nowrap;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    pointer-events: none;
                ">${field.id}</div>`,
                iconSize: [20, 20],
                iconAnchor: [10, -10]
            })

            const label = L.marker([field.lat, field.lon], {
                icon: labelIcon,
                interactive: false
            }).addTo(mapRef.current!)

            marker.bindPopup(`
                <div style="font-size: 13px; color: #111827;">
                    <strong>Field ${field.id}</strong><br/>
                    <span style="color: #374151;">
                    Yield: ${field.demand} tons<br/>
                    Service: ${field.serviceTimeMinutes} min
                    </span>
                </div>
            `)

            fieldMarkersRef.current.push(marker)
            fieldMarkersRef.current.push(label as L.Marker)
        })
    }, [fields])

    // Polyline decoder
    const decodePolyline = (encoded: string): [number, number][] => {
        const coordinates: [number, number][] = []
        let index = 0
        let lat = 0
        let lng = 0

        while (index < encoded.length) {
            let b: number
            let shift = 0
            let result = 0

            do {
                b = encoded.charCodeAt(index++) - 63
                result |= (b & 0x1f) << shift
                shift += 5
            } while (b >= 0x20)

            const dlat = (result & 1) !== 0 ? ~(result >> 1) : result >> 1
            lat += dlat

            shift = 0
            result = 0

            do {
                b = encoded.charCodeAt(index++) - 63
                result |= (b & 0x1f) << shift
                shift += 5
            } while (b >= 0x20)

            const dlng = (result & 1) !== 0 ? ~(result >> 1) : result >> 1
            lng += dlng

            coordinates.push([lat / 1e5, lng / 1e5])
        }

        return coordinates
    }

    // Update routes
    useEffect(() => {
        if (!mapRef.current) return

        // Remove old route layers
        routeLayersRef.current.forEach(layer => layer.remove())
        routeLayersRef.current = []

        if (!routes || !routes.routes) return

        // Draw routes
        routes.routes.forEach((route: OrsRoute, idx: number) => {
            const vehicle = vehicles[idx]
            if (!vehicle) return

            let coordinates: [number, number][] = []

            // Handle different geometry formats
            if (route.geometry) {
                if (typeof route.geometry === 'string') {
                    // Encoded polyline - decode it
                    try {
                        coordinates = decodePolyline(route.geometry)
                    } catch (e) {
                        console.warn('Failed to decode polyline:', e)
                    }
                } else if (typeof route.geometry === 'object' && route.geometry.coordinates) {
                    // GeoJSON format [lon, lat] - flip to [lat, lon]
                    coordinates = route.geometry.coordinates.map((coord: number[]) =>
                        [coord[1], coord[0]] as [number, number]
                    )
                }
            }

            // If no geometry, try to build from steps
            if (coordinates.length === 0 && route.steps && Array.isArray(route.steps)) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                route.steps.forEach((step: any) => {
                    if (step.location && Array.isArray(step.location)) {
                        coordinates.push([step.location[1], step.location[0]])
                    }
                })
            }

            if (coordinates.length > 0) {
                const routeLine = L.polyline(coordinates, {
                    color: vehicle.color,
                    weight: 5,
                    opacity: 0.85,
                    lineJoin: 'round',
                    lineCap: 'round'
                }).addTo(mapRef.current!)

                routeLine.bindPopup(`
                    <div style="font-size: 13px; color: #111827;">
                        <strong>${vehicle.name}</strong><br/>
                        <span style="color: #374151;">
                        Distance: ${((route.distance || 0) / 1000).toFixed(2)} km<br/>
                        Duration: ${((route.duration || 0) / 60).toFixed(0)} min<br/>
                        Stops: ${route.steps?.length || 0}
                        </span>
                    </div>
                `)

                routeLayersRef.current.push(routeLine)
            }
        })

        // Fit map to show all routes if available
        if (routeLayersRef.current.length > 0) {
            const group = L.featureGroup(routeLayersRef.current)
            mapRef.current.fitBounds(group.getBounds(), { padding: [50, 50] })
        }
    }, [routes, vehicles])

    return (
        <div
            id="route-optimization-map"
            className="w-full h-full"
        />
    )
}
