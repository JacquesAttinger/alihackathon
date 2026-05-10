import { useState, useRef, useEffect, useCallback } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import './App.css'
import type { RouteModule } from './types'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type Coord = [number, number]
type Suggestion = { place_name: string; center: Coord }
type RouteResult = {
  park_name: string | null
  walking_minutes: number
  route: { geometry: { coordinates: Coord[] } }
}

async function geocode(query: string): Promise<Suggestion[]> {
  const token = import.meta.env.VITE_MAPBOX_TOKEN
  const res = await fetch(
    `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json` +
    `?access_token=${token}&country=us&proximity=-87.6298,41.8781&types=address,poi`
  )
  const data = await res.json()
  return data.features?.map((f: { place_name: string; center: Coord }) => ({
    place_name: f.place_name,
    center: f.center,
  })) ?? []
}

async function reverseGeocode(coord: Coord): Promise<string> {
  const token = import.meta.env.VITE_MAPBOX_TOKEN
  const res = await fetch(
    `https://api.mapbox.com/geocoding/v5/mapbox.places/${coord[0]},${coord[1]}.json` +
    `?access_token=${token}&types=address,poi&limit=1`
  )
  const data = await res.json()
  return data.features?.[0]?.place_name ?? `${coord[1].toFixed(5)}, ${coord[0].toFixed(5)}`
}

function AddressInput({
  label, value, onChange, onSelect, color,
}: {
  label: string; value: string; onChange: (v: string) => void
  onSelect: (s: Suggestion) => void; color: string
}) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [open, setOpen] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleChange = (v: string) => {
    onChange(v)
    if (timer.current) clearTimeout(timer.current)
    if (v.length < 3) { setSuggestions([]); setOpen(false); return }
    timer.current = setTimeout(async () => {
      const results = await geocode(v)
      setSuggestions(results)
      setOpen(results.length > 0)
    }, 300)
  }

  return (
    <div className="input-wrapper">
      <div className="input-label-row">
        <span className="pin-dot" style={{ background: color }} />
        <label>{label}</label>
      </div>
      <input
        value={value}
        onChange={e => handleChange(e.target.value)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder="Search or click map to place pin"
      />
      {open && (
        <ul className="suggestions">
          {suggestions.map((s, i) => (
            <li key={i} onMouseDown={() => { onSelect(s); onChange(s.place_name); setOpen(false) }}>
              {s.place_name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

type PinMode = 'start' | 'end' | null

interface Props {
  module: RouteModule | null
  onBack: () => void
}

export default function MapView({ module, onBack }: Props) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const startMarker = useRef<mapboxgl.Marker | null>(null)
  const endMarker = useRef<mapboxgl.Marker | null>(null)
  const pinMode = useRef<PinMode>(null)

  const [startText, setStartText] = useState('')
  const [endText, setEndText] = useState('')
  const [startCoord, setStartCoord] = useState<Coord | null>(null)
  const [endCoord, setEndCoord] = useState<Coord | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RouteResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [clickHint, setClickHint] = useState<string | null>(null)

  const setPin = useCallback(async (coord: Coord, type: 'start' | 'end') => {
    if (!map.current) return
    const isStart = type === 'start'
    const color = isStart ? '#22c55e' : '#ef4444'
    const markerRef = isStart ? startMarker : endMarker

    if (markerRef.current) {
      markerRef.current.setLngLat(coord)
    } else {
      markerRef.current = new mapboxgl.Marker({ color, draggable: true })
        .setLngLat(coord)
        .addTo(map.current)

      markerRef.current.on('dragend', async () => {
        const lngLat = markerRef.current!.getLngLat()
        const newCoord: Coord = [lngLat.lng, lngLat.lat]
        if (isStart) {
          setStartCoord(newCoord)
          setStartText(await reverseGeocode(newCoord))
        } else {
          setEndCoord(newCoord)
          setEndText(await reverseGeocode(newCoord))
        }
        setResult(null)
      })
    }

    if (isStart) {
      setStartCoord(coord)
      setStartText(await reverseGeocode(coord))
    } else {
      setEndCoord(coord)
      setEndText(await reverseGeocode(coord))
    }
    setResult(null)
  }, [])

  const handleMapClick = useCallback((e: mapboxgl.MapMouseEvent) => {
    const coord: Coord = [e.lngLat.lng, e.lngLat.lat]
    if (pinMode.current) {
      setPin(coord, pinMode.current)
      pinMode.current = null
      setClickHint(null)
    } else if (!startMarker.current) {
      setPin(coord, 'start')
      setClickHint('Now click to place your destination pin')
    } else if (!endMarker.current) {
      setPin(coord, 'end')
      setClickHint(null)
    } else {
      const startLL = startMarker.current!.getLngLat()
      const endLL = endMarker.current!.getLngLat()
      const dStart = Math.hypot(coord[0] - startLL.lng, coord[1] - startLL.lat)
      const dEnd = Math.hypot(coord[0] - endLL.lng, coord[1] - endLL.lat)
      setPin(coord, dStart < dEnd ? 'start' : 'end')
    }
  }, [setPin])

  useEffect(() => {
    if (map.current) return
    const m = new mapboxgl.Map({
      container: mapContainer.current!,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [-87.6298, 41.8781],
      zoom: 13,
    })
    m.addControl(new mapboxgl.NavigationControl(), 'bottom-right')
    m.on('click', handleMapClick)
    m.getCanvas().style.cursor = 'crosshair'
    map.current = m
  }, [handleMapClick])

  const drawRoute = useCallback((coords: Coord[]) => {
    if (!map.current) return
    const geojson: GeoJSON.Feature<GeoJSON.LineString> = {
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: coords },
      properties: {},
    }
    const source = map.current.getSource('route') as mapboxgl.GeoJSONSource | undefined
    if (source) {
      source.setData(geojson)
    } else {
      map.current.addSource('route', { type: 'geojson', data: geojson })
      map.current.addLayer({
        id: 'route-shadow',
        type: 'line',
        source: 'route',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: { 'line-color': '#000', 'line-width': 9, 'line-opacity': 0.3 },
      })
      map.current.addLayer({
        id: 'route',
        type: 'line',
        source: 'route',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: { 'line-color': '#6366f1', 'line-width': 5, 'line-opacity': 0.9 },
      })
    }
    const bounds = coords.reduce(
      (b, c) => b.extend(c as mapboxgl.LngLatLike),
      new mapboxgl.LngLatBounds(coords[0], coords[0])
    )
    map.current.fitBounds(bounds, { padding: 100 })
  }, [])

  const findRoute = async () => {
    if (!startCoord || !endCoord) { setError('Place both pins on the map first.'); return }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch(`${API_URL}/api/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_lat: startCoord[1], start_lng: startCoord[0],
          end_lat: endCoord[1], end_lng: endCoord[0],
        }),
      })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Route failed') }
      const data: RouteResult = await res.json()
      drawRoute(data.route.geometry.coordinates)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSelect = useCallback((type: 'start' | 'end') => (s: Suggestion) => {
    setPin(s.center, type)
    map.current?.flyTo({ center: s.center, zoom: 15 })
  }, [setPin])

  const activatePinMode = (type: PinMode) => {
    pinMode.current = type
    setClickHint(`Click anywhere on the map to place the ${type} pin`)
  }

  return (
    <div className="app">
      <div ref={mapContainer} className="map" />
      {clickHint && <div className="click-hint">{clickHint}</div>}

      <div className="panel">
        <div className="panel-top-row">
          <button className="back-btn" onClick={onBack}>← Modules</button>
          {module && (
            <div className="module-pill" style={{ background: module.bg, color: module.color }}>
              {module.icon} {module.name}
            </div>
          )}
        </div>

        <div className="panel-header">
          <h1>Routify</h1>
          <p>Chicago's safest walking routes</p>
        </div>

        <div className="pin-instructions">
          Click the map to place pins, or search below. Drag pins to adjust.
        </div>

        <div className="input-group">
          <AddressInput
            label="Start"
            value={startText}
            onChange={setStartText}
            onSelect={handleSearchSelect('start')}
            color="#22c55e"
          />
          <button className="pin-btn" onClick={() => activatePinMode('start')}>Drop Pin</button>
        </div>

        <div className="input-group">
          <AddressInput
            label="Destination"
            value={endText}
            onChange={setEndText}
            onSelect={handleSearchSelect('end')}
            color="#ef4444"
          />
          <button className="pin-btn" onClick={() => activatePinMode('end')}>Drop Pin</button>
        </div>

        <button
          className="route-btn"
          onClick={findRoute}
          disabled={loading || !startCoord || !endCoord}
        >
          {loading ? 'Finding safe route…' : 'Find Safe Route'}
        </button>

        {error && <div className="error-msg">{error}</div>}

        {result && (
          <div className="result">
            <div className="walk-time">{result.walking_minutes} min walk</div>
            {result.park_name && (
              <div className="breakdown">
                <div className="breakdown-item">
                  <span className="bi-icon">🌳</span>
                  <span>Routed through <strong>{result.park_name}</strong></span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
