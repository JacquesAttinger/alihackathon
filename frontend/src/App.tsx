import { useState, useRef, useEffect, useCallback } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import './App.css'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type Suggestion = { place_name: string; center: [number, number] }
type SafetyBreakdown = { lighting: string; crime: string; businesses: string; dead_zones: string }
type RouteResult = { safety_score: number; walking_minutes: number; breakdown: SafetyBreakdown; route: { geometry: { coordinates: [number, number][] } } }

async function geocode(query: string): Promise<Suggestion[]> {
  const token = import.meta.env.VITE_MAPBOX_TOKEN
  const res = await fetch(
    `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${token}&country=us&proximity=-87.6298,41.8781&types=address,poi`
  )
  const data = await res.json()
  return data.features?.map((f: { place_name: string; center: [number, number] }) => ({
    place_name: f.place_name,
    center: f.center,
  })) ?? []
}

function AddressInput({
  label,
  value,
  onChange,
  onSelect,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  onSelect: (s: Suggestion) => void
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
      <label>{label}</label>
      <input
        value={value}
        onChange={e => handleChange(e.target.value)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder={`Enter ${label.toLowerCase()}`}
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

export default function App() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const startMarker = useRef<mapboxgl.Marker | null>(null)
  const endMarker = useRef<mapboxgl.Marker | null>(null)

  const [startText, setStartText] = useState('')
  const [endText, setEndText] = useState('')
  const [startCoord, setStartCoord] = useState<[number, number] | null>(null)
  const [endCoord, setEndCoord] = useState<[number, number] | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<RouteResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (map.current) return
    map.current = new mapboxgl.Map({
      container: mapContainer.current!,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-87.6298, 41.8781],
      zoom: 13,
    })
    map.current.addControl(new mapboxgl.NavigationControl(), 'bottom-right')
  }, [])

  const placeMarker = useCallback((coord: [number, number], type: 'start' | 'end') => {
    if (!map.current) return
    const color = type === 'start' ? '#22c55e' : '#ef4444'
    if (type === 'start') {
      startMarker.current?.remove()
      startMarker.current = new mapboxgl.Marker({ color }).setLngLat(coord).addTo(map.current)
    } else {
      endMarker.current?.remove()
      endMarker.current = new mapboxgl.Marker({ color }).setLngLat(coord).addTo(map.current)
    }
    map.current.flyTo({ center: coord, zoom: 14 })
  }, [])

  const drawRoute = useCallback((coords: [number, number][]) => {
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
        paint: { 'line-color': '#22c55e', 'line-width': 5, 'line-opacity': 0.95 },
      })
    }
    const bounds = coords.reduce(
      (b, c) => b.extend(c as mapboxgl.LngLatLike),
      new mapboxgl.LngLatBounds(coords[0], coords[0])
    )
    map.current.fitBounds(bounds, { padding: 100 })
  }, [])

  const findRoute = async () => {
    if (!startCoord || !endCoord) { setError('Please select both a start and destination.'); return }
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

  const scoreColor = (score: number) =>
    score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'

  return (
    <div className="app">
      <div ref={mapContainer} className="map" />

      <div className="panel">
        <div className="panel-header">
          <h1>SafeWalk</h1>
          <p>Chicago's safest walking routes</p>
        </div>

        <AddressInput
          label="Start"
          value={startText}
          onChange={setStartText}
          onSelect={s => { setStartCoord(s.center); placeMarker(s.center, 'start') }}
        />
        <AddressInput
          label="Destination"
          value={endText}
          onChange={setEndText}
          onSelect={s => { setEndCoord(s.center); placeMarker(s.center, 'end') }}
        />

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
            <div className="score-row">
              <span className="score-label">Safety Score</span>
              <span className="score-value" style={{ color: scoreColor(result.safety_score) }}>
                {result.safety_score}/100
              </span>
            </div>
            <div className="walk-time">{result.walking_minutes} min walk</div>
            <div className="breakdown">
              <div className="breakdown-item">
                <span className="bi-icon">💡</span>
                <span>{result.breakdown.lighting}</span>
              </div>
              <div className="breakdown-item">
                <span className="bi-icon">🔒</span>
                <span>{result.breakdown.crime}</span>
              </div>
              <div className="breakdown-item">
                <span className="bi-icon">🏪</span>
                <span>{result.breakdown.businesses}</span>
              </div>
              <div className="breakdown-item">
                <span className="bi-icon">⚠️</span>
                <span>{result.breakdown.dead_zones}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
