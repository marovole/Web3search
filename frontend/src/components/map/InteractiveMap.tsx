/**
 * Interactive Investment Map Component
 * Displays crypto projects and investments on an interactive map
 * Part of Phase 4: Interactive Investment Map
 */

import { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { formatMarketCap } from '@/lib/safeFormatters'

// Fix for default marker icons in Leaflet with webpack/vite
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

L.Marker.prototype.options.icon = DefaultIcon

export interface MapProject {
  id: string
  name: string
  lat: number
  lng: number
  category: 'defi' | 'nft' | 'gaming' | 'infrastructure' | 'dao'
  description: string
  marketCap?: number
  logo?: string
  website?: string
  foundedYear?: number
}

export interface InteractiveMapProps {
  projects: MapProject[]
  center?: [number, number]
  zoom?: number
  onProjectClick?: (project: MapProject) => void
  onMapClick?: (lat: number, lng: number) => void
  className?: string
}

/**
 * Map controller component for handling map events
 */
function MapController({
  onMapClick,
  center,
  zoom,
}: {
  onMapClick?: (lat: number, lng: number) => void
  center?: [number, number]
  zoom?: number
}) {
  const map = useMap()

  // Update map view when center or zoom changes
  useEffect(() => {
    if (center) {
      map.setView(center, zoom || 10)
    }
  }, [map, center, zoom])

  // Handle map click events
  useEffect(() => {
    if (!onMapClick) return

    const handleClick = (e: L.LeafletMouseEvent) => {
      onMapClick(e.latlng.lat, e.latlng.lng)
    }

    map.on('click', handleClick)
    return () => {
      map.off('click', handleClick)
    }
  }, [map, onMapClick])

  return null
}

/**
 * Get marker color based on project category
 */
function getMarkerColor(category: MapProject['category']) {
  switch (category) {
    case 'defi':
      return '#3B82F6' // blue
    case 'nft':
      return '#8B5CF6' // purple
    case 'gaming':
      return '#EF4444' // red
    case 'infrastructure':
      return '#10B981' // green
    case 'dao':
      return '#F59E0B' // amber
    default:
      return '#6B7280' // gray
  }
}

/**
 * Create custom marker icon based on category
 */
function createCustomIcon(category: MapProject['category']) {
  const color = getMarkerColor(category)

  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: 30px;
        height: 30px;
        background-color: ${color};
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
      ">
        ${category.charAt(0).toUpperCase()}
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  })
}

export function InteractiveMap({
  projects,
  center = [40.7128, -74.0060], // Default: New York
  zoom = 2,
  onProjectClick,
  onMapClick,
  className = '',
}: InteractiveMapProps) {
  const [selectedProject, setSelectedProject] = useState<MapProject | null>(null)
  const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null)

  // Handle marker click
  const handleMarkerClick = useCallback(
    (project: MapProject) => {
      setSelectedProject(project)
      onProjectClick?.(project)
    },
    [onProjectClick]
  )

  // Filter projects based on map bounds (performance optimization)
  const visibleProjects = projects.filter((project) => {
    if (!mapBounds) return true
    return mapBounds.contains([project.lat, project.lng])
  })

  // Handle map bounds change
  const handleBoundsChange = useCallback((bounds: L.LatLngBounds) => {
    setMapBounds(bounds)
  }, [])

  return (
    <div className={`w-full h-full relative ${className}`}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        className="rounded-lg z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapController
          onMapClick={onMapClick}
          center={center}
          zoom={zoom}
        />

        {/* Project Markers */}
        {visibleProjects.map((project) => (
          <Marker
            key={project.id}
            position={[project.lat, project.lng]}
            icon={createCustomIcon(project.category)}
            eventHandlers={{
              click: () => handleMarkerClick(project),
            }}
          >
            <Popup className="custom-popup">
              <div className="min-w-64 p-2">
                <div className="flex items-start space-x-3">
                  {project.logo && (
                    <img
                      src={project.logo}
                      alt={project.name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  )}
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {project.name}
                    </h3>
                    <span
                      className="inline-block mt-1 px-2 py-1 text-xs font-medium rounded-full"
                      style={{
                        backgroundColor: getMarkerColor(project.category) + '20',
                        color: getMarkerColor(project.category),
                      }}
                    >
                      {project.category.toUpperCase()}
                    </span>
                  </div>
                </div>

                <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
                  {project.description}
                </p>

                <div className="mt-3 space-y-1">
                  {project.marketCap && (
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <span className="font-medium">Market Cap:</span> {formatMarketCap(project.marketCap)}
                    </p>
                  )}
                  {project.foundedYear && (
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <span className="font-medium">Founded:</span> {project.foundedYear}
                    </p>
                  )}
                </div>

                <div className="mt-4 flex space-x-2">
                  {project.website && (
                    <a
                      href={project.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Visit Website →
                    </a>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Map Bounds Tracker for Performance */}
        <MapBoundsTracker onBoundsChange={handleBoundsChange} />
      </MapContainer>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
          Project Categories
        </h3>
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3B82F6' }} />
            <span className="text-xs text-gray-600 dark:text-gray-400">DeFi</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#8B5CF6' }} />
            <span className="text-xs text-gray-600 dark:text-gray-400">NFT</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#EF4444' }} />
            <span className="text-xs text-gray-600 dark:text-gray-400">Gaming</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#10B981' }} />
            <span className="text-xs text-gray-600 dark:text-gray-400">Infrastructure</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#F59E0B' }} />
            <span className="text-xs text-gray-600 dark:text-gray-400">DAO</span>
          </div>
        </div>
      </div>

      {/* Selected Project Info Panel */}
      {selectedProject && (
        <div className="absolute bottom-4 left-4 right-4 md:right-auto bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10 max-w-md">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {selectedProject.name}
              </h3>
              <span
                className="inline-block mt-1 px-2 py-1 text-xs font-medium rounded-full"
                style={{
                  backgroundColor: getMarkerColor(selectedProject.category) + '20',
                  color: getMarkerColor(selectedProject.category),
                }}
              >
                {selectedProject.category.toUpperCase()}
              </span>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {selectedProject.description}
              </p>
            </div>
            <button
              onClick={() => setSelectedProject(null)}
              className="ml-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ✕
            </button>
          </div>
          <div className="mt-3 flex space-x-2">
            {selectedProject.website && (
              <a
                href={selectedProject.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Visit Website →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Track map bounds changes for performance optimization
 */
function MapBoundsTracker({
  onBoundsChange,
}: {
  onBoundsChange: (bounds: L.LatLngBounds) => void
}) {
  const map = useMap()

  useEffect(() => {
    const handleMoveEnd = () => {
      onBoundsChange(map.getBounds())
    }

    map.on('moveend', handleMoveEnd)
    // Initialize bounds
    onBoundsChange(map.getBounds())

    return () => {
      map.off('moveend', handleMoveEnd)
    }
  }, [map, onBoundsChange])

  return null
}

export default InteractiveMap
