from .google_places_base import GooglePlacesBase


class NightlifeDensity(GooglePlacesBase):
    key = "nightlife_density"
    place_type = "bar"
    search_radius = 300
    grid_max = 6.0
