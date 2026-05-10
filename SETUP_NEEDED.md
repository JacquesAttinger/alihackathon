# Things You Need To Do Before All Parameters Work

## Already Working (no action needed)
- Violent crime, property crime — Chicago Data Portal, no key
- Park proximity, tree canopy, transit (CTA), blight 311, public art, landmarks — Chicago Data Portal, no key
- Lakefront/riverwalk detection — OSM tags, no key
- All Tier 3 OSM parameters (road type, sidewalk, dead zones, alleys, etc.) — no key
- All Tier 4 composite parameters — computed from the above

---

## 1. Google Places API — already have key, needs enabling

**What it unlocks:** restaurant density, nightlife density, coffee shops, open businesses (4 parameters)

**Status:** Key is saved in `.env`. You need to make sure these APIs are enabled in Google Cloud Console:
- Go to `console.cloud.google.com`
- Search and enable: **Places API (New)** or **Places API**

That's it — the code will pick up the key automatically.

**Cost estimate:** The loader samples the city in a grid. At ~500 grid cells × 4 place types = ~2,000 API calls at startup. Google's free tier covers 1,000 calls/month; this will likely cost ~$3–5 per server restart. For a hackathon: acceptable. For production: add caching to disk.

---

## 2. Foursquare API — need a free account

**What it unlocks:** foot_traffic parameter (busyness/crowd data)

**How to get:**
1. Go to `foursquare.com/developer`
2. Create a free account → create an app
3. Copy the **API Key**
4. Add to `.env`:
   ```
   FOURSQUARE_API_KEY=your_key_here
   ```

**Fallback:** If no key, foot_traffic automatically falls back to averaging restaurant + nightlife density. Functional but less accurate.

**Cost:** Free tier is generous for our usage.

---

## 3. Socrata App Token — optional but recommended

**What it unlocks:** Faster, higher-rate-limit access to all Chicago Data Portal datasets (crime, trees, lights, etc.)

**How to get:**
1. Go to `data.cityofchicago.org`
2. Sign up for a free account → go to Developer Settings → Create New App Token
3. Add to `.env`:
   ```
   SOCRATA_APP_TOKEN=your_token_here
   ```

**Without it:** Datasets still load, but at a lower rate limit. Fine for development; may be slow or throttled in production.

---

## Summary Table

| Parameter(s) | Status | Action needed |
|---|---|---|
| violent_crime, property_crime | ✅ Working | None |
| street_lights | ✅ Working | None |
| park_proximity, tree_canopy | ✅ Working | None |
| transit_proximity | ✅ Working | None |
| blight_311, public_art, landmarks | ✅ Working | None |
| lakefront_access | ✅ Working | None |
| All Tier 3 OSM params (9 params) | ✅ Working | None |
| All Tier 4 composites (9 params) | ✅ Working | (depends on above) |
| restaurant_density | ⚠️ Needs Places API enabled | Enable in Google Cloud Console |
| nightlife_density | ⚠️ Needs Places API enabled | Enable in Google Cloud Console |
| coffee_shop_density | ⚠️ Needs Places API enabled | Enable in Google Cloud Console |
| open_businesses | ⚠️ Needs Places API enabled | Enable in Google Cloud Console |
| foot_traffic | ⚠️ Optional Foursquare key | Create free Foursquare account |
