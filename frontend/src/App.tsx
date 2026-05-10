import { useState } from 'react'
import type { RouteModule } from './types'
import HomePage from './HomePage'
import MapView from './MapView'

export default function App() {
  const [page, setPage] = useState<'home' | 'map'>('home')
  const [activeModule, setActiveModule] = useState<RouteModule | null>(null)

  if (page === 'home') {
    return (
      <HomePage
        onStart={mod => {
          setActiveModule(mod)
          setPage('map')
        }}
      />
    )
  }

  return <MapView module={activeModule} onBack={() => setPage('home')} />
}
