"""
Open businesses right now — uses Google Places open_now filter.
Requires: GOOGLE_PLACES_API_KEY
"""
from .google_places_base import GooglePlacesBase


class OpenBusinesses(GooglePlacesBase):
    key = "open_businesses"
    place_type = "establishment"
    search_radius = 150
    open_now = True
    grid_max = 10.0
    sample_every_n_cells = 4
