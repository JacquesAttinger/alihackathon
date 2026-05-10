# Project: SafeWalk (working title)

> **How to use this doc:** Sections marked with `[ FILL IN ]` need your input before we build. Everything else is a proposed plan — push back on anything that doesn't match your vision.

---

## 1. What We're Building

A web app where a user enters a start and end location and receives the **safest walking route** between them — not the fastest. The interface feels like Uber: type in locations, see a route on a map, understand why it's safe. A safety score or summary (e.g., "This route is well-lit and passes 5 open businesses") will accompany each route.

### Target User
`[ FILL IN ]` — Who is the primary user? Examples:
- A woman walking home alone at night in a big city
- A tourist unfamiliar with a neighborhood
- Anyone who prioritizes personal safety over speed

### Target City / Geography
`[ FILL IN ]` — What city should we focus on first? (Narrowing this down determines which crime and lighting datasets we can access.) Options:
- San Francisco, CA
- New York City, NY
- Chicago, IL
- Los Angeles, CA
- Other: ___________

---

## 2. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React + TypeScript | Industry standard, large community, good for map UIs |
| **Map UI** | Mapbox GL JS | Beautiful maps, great routing UI, free tier available |
| **Backend** | Python + FastAPI | Fast to build, excellent geospatial libraries |
| **Routing Engine** | OSMnx + NetworkX | Builds a street graph from OpenStreetMap and runs our custom algorithm on it |
| **Database** | PostgreSQL + PostGIS | Industry-standard geospatial database |
| **Crime/POI Cache** | Redis (optional) | Speeds up repeated lookups on frequently-requested areas |
| **Hosting (frontend)** | Vercel | Free, one-click deploys |
| **Hosting (backend)** | Railway or Render | Free tier, easy Python deploys |

**Fallback / simpler option (if time is short):** Skip the custom backend entirely and use the **Google Maps Directions API** with a lightweight Node.js proxy. We lose algorithm customization but ship faster.

---

## 3. Architecture Overview

```
User's Browser (React + Mapbox)
        |
        | HTTP request: { start, end, time_of_day }
        v
FastAPI Backend
        |
        |--- OSMnx: Load street graph for the area
        |--- Safety Scorer: Attach weights to each street segment
        |       |--- Crime data layer
        |       |--- Lighting data layer
        |       |--- Business density layer (Google Places API)
        |       |--- Dead-zone detection (OSM land use)
        |
        |--- NetworkX: Run modified Dijkstra's algorithm
        |       (minimize safety cost, not just distance)
        |
        v
Return: GeoJSON route + safety score breakdown
        |
        v
Mapbox renders the route on the map
```

---

## 4. Algorithm Design

### How It Works
We model the city as a **graph**: intersections are nodes, street segments are edges. Each edge gets a **safety cost** (low = safer). We run a shortest-path algorithm that minimizes total safety cost, not distance.

### Safety Cost Formula (per street segment)
```
safety_cost = distance_meters
            × lighting_penalty        (1.0–2.5)
            × crime_penalty           (1.0–3.0)
            × dead_zone_penalty       (1.0–5.0)
            ÷ business_density_boost  (1.0–1.5)
            ÷ open_now_boost          (1.0–1.3)
            × crowd_penalty           (1.0–1.5)
```
Penalty > 1 = more dangerous. Boost < 1 = safer. Values above are starting points — we will tune these.

### Algorithm Parameters (Full List)

#### Confirmed (from original plan)
| Parameter | Description | Data Source |
|---|---|---|
| **Lighting** | Is the street well-lit at night? | City street light datasets, satellite night imagery |
| **Crime patterns** | Historical crime density by block | City open data portals (see Section 6) |
| **Business density** | "Eyes on the street" — more storefronts = safer | Google Places API, OpenStreetMap |
| **Time sensitivity** | Weight penalties heavier at night | Passed in by user at request time |
| **Crowd/busyness** | How many people are around? | Google Popular Times (unofficial), Foursquare |
| **Open Now boost** | 3+ open businesses within 100m → safety boost | Google Places API (`open_now` filter) |
| **Dead zone penalty** | Industrial areas, parks at night, vacant blocks | OpenStreetMap land-use tags |

#### Proposed Additions
| Parameter | Description | Data Source |
|---|---|---|
| **Proximity to emergency services** | Closeness to a police station, fire station, or hospital | OpenStreetMap, Google Places API |
| **Sidewalk existence** | Does a sidewalk actually exist on this segment? | OpenStreetMap `sidewalk` tags |
| **Street width / visibility** | Wide, open streets feel safer than narrow alleys | OpenStreetMap `width` tags |
| **Traffic volume** | More cars = more witnesses; also signals a main road | OpenStreetMap road type (`highway` tag) |
| **Cell signal coverage** | Dead zones with no signal are riskier | FCC coverage maps, OpenSignal API |
| **Construction zones** | Active construction = poor lighting, reduced foot traffic | City permit APIs (where available) |
| **Nightlife proximity** | Bars/clubs near closing time → higher incident risk | Google Places `type=bar`, time-gated |
| **Crosswalk safety** | Signalized crossings safer than unmarked ones | OpenStreetMap `crossing` tags |
| **User-reported incidents** | Crowdsourced data from our own users (future feature) | Our own database |
| **Vegetation/visibility** | Dense tree canopy can obscure visibility at night | OpenStreetMap `natural` tags, satellite imagery |

`[ FILL IN ]` — Are there any parameters you want to **prioritize** or **remove**? Do any feel wrong for your target user?

### Algorithm: Modified Dijkstra's / A*
We'll use **NetworkX's** `shortest_path` with custom edge weights (the safety cost above). For larger cities we may switch to **A*** for speed.

---

## 5. User Interface

### Core Flow
1. User lands on page — sees a full-screen map (Mapbox)
2. Two input boxes: **Start** and **Destination** (with autocomplete)
3. Optional: **Time of day** slider or "Right now" toggle
4. Click **"Find Safe Route"**
5. Route appears on map, highlighted in green
6. Side panel shows:
   - Safety score (e.g., 84/100)
   - What's working in your favor ("Well-lit", "Busy street", "Police station nearby")
   - What to watch out for ("Passes through 1 low-traffic block")
   - Estimated walking time

### Uber-Like Feel
- Dark map theme
- Smooth animated route drawing
- Minimal UI — map is the hero
- Mobile-first responsive layout

`[ FILL IN ]` — Any UI features you want to add? Examples:
- "Compare routes" (show safe route vs. fast route)
- Save favorite routes
- Share a route link
- Report an incident on the route

---

## 6. Data Sources

### Crime Data
| City | Source | URL |
|---|---|---|
| San Francisco | DataSF (Socrata) | data.sfgov.org |
| New York City | NYC OpenData | data.cityofnewyork.us |
| Chicago | Chicago Data Portal | data.cityofchicago.org |
| Los Angeles | LAPD Open Data | data.lacity.org |
| Most US cities | Socrata platform | `[ FILL IN city name ]` |

We will download crime incident CSVs, aggregate by street segment, and store in our PostGIS database. We can also try the **SpotCrime API** as a unified source across cities.

### Street / Map Data
- **OpenStreetMap** via OSMnx — free, global, updated constantly
- Gives us: street network, sidewalks, land use, building types, crosswalks

### Business / Places Data
- **Google Places API** — accurate, has `open_now`, has business categories
  - Cost: ~$17 per 1,000 requests (free $200/month credit from Google)
- **Yelp Fusion API** — free tier (500 calls/day), good for business hours

### Lighting Data
- **City street light datasets** — many cities publish shapefiles of light locations
  - SF: `data.sfgov.org` → search "street lights"
  - NYC: NYC Open Data → "Street Light Outage"
- **Fallback**: Use road type as proxy (major roads assumed lit, alleys not)

### Busyness / Foot Traffic
- **Google Popular Times** — embedded in Google Maps; no official API, but scrapers exist (`populartimes` Python library)
- **Foursquare Places API** — has foot traffic data, free tier available
- **Pedestrian count data** — some cities publish this as open data

`[ FILL IN ]` — Do you have access to any API keys already? (Google Maps, Mapbox, Yelp)?

---

## 7. Development Phases

### Phase 1 — Proof of Concept (Day 1)
- [ ] Set up React frontend with Mapbox map
- [ ] User can enter start/end, see a basic route (even just Google Maps Directions API)
- [ ] Backend returns mock safety score

### Phase 2 — Core Algorithm (Day 1–2)
- [ ] Load OSM street graph for target city with OSMnx
- [ ] Pull crime data and attach to street segments
- [ ] Run modified Dijkstra's — return safest route
- [ ] Display actual route on map

### Phase 3 — Enrich the Algorithm (Day 2)
- [ ] Add lighting layer
- [ ] Add Google Places business density and "Open Now" boost
- [ ] Add dead-zone detection (OSM land use)
- [ ] Add time-of-day weighting

### Phase 4 — Polish UI (Day 2–3)
- [ ] Safety score display
- [ ] "Why is this safe?" breakdown panel
- [ ] Mobile responsiveness
- [ ] Clean, Uber-like design

### Stretch Goals
- [ ] User accounts and saved routes
- [ ] Incident reporting
- [ ] Multiple route options (safest / balanced / fastest)
- [ ] Real-time crowd data integration

---

## 8. Open Questions — Please Fill In

1. **Project name:** What should we call this? (SafeWalk, GuardRoute, SafeStep, your idea?)

2. **Target city:** Which city for the demo / MVP? ___________

3. **Primary user:** Who are we building for, specifically? ___________

4. **API keys:** Do you have (or can you create) accounts for:
   - [ ] Google Cloud Platform (for Maps + Places API)
   - [ ] Mapbox (for the map UI)
   - [ ] Yelp Fusion (optional)

5. **Algorithm priority:** Which parameters matter most to you? Rank the top 3:
   - Crime data
   - Lighting
   - Business density / Open Now
   - Dead zones
   - Other: ___________

6. **Time of day:** Should the app default to "right now" using the user's device clock, or let them pick manually?

7. **Route comparison:** Do you want to show both the "safest" route AND the "fastest" route so users can see the trade-off?

8. **Mobile vs. Desktop:** Is this primarily a mobile app (walking = phone in hand) or desktop?

9. **Any features you've seen in other apps** that you want to include or deliberately avoid?

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Crime data isn't available for target city | Fall back to SpotCrime API or use a city where data exists |
| Google Places API costs money | Cache aggressively, use OSM as fallback |
| OSMnx street graph is slow to load | Pre-process and store the graph for the target city at startup |
| Algorithm produces a route that's wildly longer than shortest | Cap the safety detour at +50% distance; show both routes |
| Lighting data is unavailable | Use road type as proxy (major arterials assumed lit) |

---

*Last updated: 2026-05-10 — Generated with Claude Code*
