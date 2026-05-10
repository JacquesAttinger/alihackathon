import type { RouteModule } from './types'

export const PRESET_MODULES: RouteModule[] = [
  {
    id: 'safe',
    name: 'Safe Route',
    description: 'Well-lit streets and low-crime areas',
    icon: '🛡️',
    color: '#6366f1',
    bg: '#eef2ff',
    preferences: { safety: true, greenery: false, kidFriendly: false, avoidTraffic: false, errand: null },
  },
  {
    id: 'green',
    name: 'Green & Scenic',
    description: 'Parks, trees, and open spaces',
    icon: '🌿',
    color: '#10b981',
    bg: '#ecfdf5',
    preferences: { safety: false, greenery: true, kidFriendly: false, avoidTraffic: false, errand: null },
  },
  {
    id: 'kids',
    name: 'Kid-Friendly',
    description: 'Quiet streets and safe crossings',
    icon: '🧒',
    color: '#f59e0b',
    bg: '#fffbeb',
    preferences: { safety: true, greenery: false, kidFriendly: true, avoidTraffic: true, errand: null },
  },
  {
    id: 'pharmacy',
    name: 'Pharmacy Stop',
    description: 'Route past a nearby pharmacy',
    icon: '💊',
    color: '#0ea5e9',
    bg: '#f0f9ff',
    preferences: { safety: false, greenery: false, kidFriendly: false, avoidTraffic: false, errand: 'pharmacy' },
  },
  {
    id: 'grocery',
    name: 'Grocery Run',
    description: 'Route past a nearby grocery store',
    icon: '🛒',
    color: '#f43f5e',
    bg: '#fff1f2',
    preferences: { safety: false, greenery: false, kidFriendly: false, avoidTraffic: false, errand: 'grocery' },
  },
]
