from .google_places_base import GooglePlacesBase


class RestaurantDensity(GooglePlacesBase):
    key = "restaurant_density"
    place_type = "restaurant"
    search_radius = 250
    grid_max = 8.0
