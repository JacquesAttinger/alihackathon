import { useState } from 'react'
import type { RouteModule, ModulePreferences, Errand } from './types'
import { PRESET_MODULES } from './presetModules'
import './HomePage.css'

const STORAGE_KEY = 'routify_custom_modules'

function loadCustomModules(): RouteModule[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveCustomModules(modules: RouteModule[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(modules))
}

const PREF_OPTIONS: { key: keyof Omit<ModulePreferences, 'errand'>; label: string; icon: string }[] = [
  { key: 'safety',       label: 'Safety first',  icon: '🛡️' },
  { key: 'greenery',     label: 'Green spaces',   icon: '🌿' },
  { key: 'kidFriendly',  label: 'Kid-friendly',   icon: '🧒' },
  { key: 'avoidTraffic', label: 'Low traffic',    icon: '🚗' },
]

const ERRAND_OPTIONS: { key: Errand; label: string; icon: string }[] = [
  { key: 'pharmacy', label: 'Pharmacy stop', icon: '💊' },
  { key: 'grocery',  label: 'Grocery run',   icon: '🛒' },
]

function buildDescription(prefs: Omit<ModulePreferences, 'errand'>, errand: Errand | null): string {
  const parts: string[] = []
  if (prefs.safety) parts.push('safe streets')
  if (prefs.greenery) parts.push('green spaces')
  if (prefs.kidFriendly) parts.push('kid-friendly')
  if (prefs.avoidTraffic) parts.push('low traffic')
  if (errand === 'pharmacy') parts.push('pharmacy stop')
  if (errand === 'grocery') parts.push('grocery stop')
  return parts.length ? parts.join(', ') : 'Custom route preferences'
}

function CreateModal({ onSave, onClose }: { onSave: (m: RouteModule) => void; onClose: () => void }) {
  const [name, setName] = useState('')
  const [prefs, setPrefs] = useState<Omit<ModulePreferences, 'errand'>>({
    safety: false, greenery: false, kidFriendly: false, avoidTraffic: false,
  })
  const [errand, setErrand] = useState<Errand | null>(null)

  const togglePref = (key: keyof typeof prefs) => setPrefs(p => ({ ...p, [key]: !p[key] }))
  const toggleErrand = (key: Errand) => setErrand(e => (e === key ? null : key))

  const handleSave = () => {
    if (!name.trim()) return
    const mod: RouteModule = {
      id: `custom-${Date.now()}`,
      name: name.trim(),
      description: buildDescription(prefs, errand),
      icon: '✨',
      color: '#8b5cf6',
      bg: '#f5f3ff',
      preferences: { ...prefs, errand },
      isCustom: true,
    }
    onSave(mod)
  }

  return (
    <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal">
        <div className="modal-header">
          <h2>Create your module</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <label className="field-label">Module name</label>
          <input
            className="modal-input"
            placeholder="e.g. Evening Stroll"
            value={name}
            onChange={e => setName(e.target.value)}
            autoFocus
          />

          <label className="field-label" style={{ marginTop: 20 }}>Priorities</label>
          <div className="chip-grid">
            {PREF_OPTIONS.map(({ key, label, icon }) => (
              <button key={key} className={`chip ${prefs[key] ? 'chip-on' : ''}`} onClick={() => togglePref(key)}>
                <span>{icon}</span>{label}
              </button>
            ))}
          </div>

          <label className="field-label" style={{ marginTop: 16 }}>
            Errand stop <span className="optional">(optional, pick one)</span>
          </label>
          <div className="chip-grid">
            {ERRAND_OPTIONS.map(({ key, label, icon }) => (
              <button key={key} className={`chip ${errand === key ? 'chip-on' : ''}`} onClick={() => toggleErrand(key)}>
                <span>{icon}</span>{label}
              </button>
            ))}
          </div>
        </div>

        <div className="modal-footer">
          <button className="modal-save" onClick={handleSave} disabled={!name.trim()}>
            Save module
          </button>
        </div>
      </div>
    </div>
  )
}

interface Props {
  onStart: (module: RouteModule | null) => void
}

export default function HomePage({ onStart }: Props) {
  const [customModules, setCustomModules] = useState<RouteModule[]>(loadCustomModules)
  const [selected, setSelected] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  const allModules = [...PRESET_MODULES, ...customModules]

  const handleSaveCustom = (mod: RouteModule) => {
    const updated = [...customModules, mod]
    setCustomModules(updated)
    saveCustomModules(updated)
    setSelected(mod.id)
    setCreating(false)
  }

  const handleStart = () => {
    const mod = allModules.find(m => m.id === selected) ?? null
    onStart(mod)
  }

  return (
    <div className="home">
      <div className="home-content">
        <div className="home-header">
          <h1 className="home-logo">Routify</h1>
          <p className="home-tagline">Plan your walk, your way</p>
        </div>

        <h2 className="home-section-title">How do you want to walk today?</h2>

        <div className="module-grid">
          {allModules.map(mod => (
            <button
              key={mod.id}
              className={`module-card ${selected === mod.id ? 'module-card-selected' : ''}`}
              onClick={() => setSelected(selected === mod.id ? null : mod.id)}
              style={selected === mod.id ? {
                borderColor: mod.color,
                boxShadow: `0 0 0 3px ${mod.color}30`,
              } : undefined}
            >
              <div className="card-icon-wrap" style={{ background: mod.bg }}>
                <span className="card-icon">{mod.icon}</span>
              </div>
              <div className="card-text">
                <span className="card-name">{mod.name}</span>
                <span className="card-desc">{mod.description}</span>
              </div>
              {mod.isCustom && <span className="custom-badge">Custom</span>}
            </button>
          ))}

          <button className="module-card create-card" onClick={() => setCreating(true)}>
            <div className="card-icon-wrap create-icon-wrap">
              <span className="card-icon create-plus">+</span>
            </div>
            <div className="card-text">
              <span className="card-name">Create module</span>
              <span className="card-desc">Build your own route style</span>
            </div>
          </button>
        </div>

        <div className="home-footer">
          <button className="start-btn" onClick={handleStart}>
            {selected
              ? `Start with ${allModules.find(m => m.id === selected)?.name}`
              : 'Start navigating'}
          </button>
          {!selected && (
            <button className="skip-btn" onClick={() => onStart(null)}>
              Skip — use default settings
            </button>
          )}
        </div>
      </div>

      {creating && <CreateModal onSave={handleSaveCustom} onClose={() => setCreating(false)} />}
    </div>
  )
}
