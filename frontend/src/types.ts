export type Errand = 'pharmacy' | 'grocery'

export type ModulePreferences = {
  safety: boolean
  greenery: boolean
  kidFriendly: boolean
  avoidTraffic: boolean
  errand: Errand | null
}

export type RouteModule = {
  id: string
  name: string
  description: string
  icon: string
  color: string
  bg: string
  preferences: ModulePreferences
  isCustom?: boolean
}
