from .google_places_base import GooglePlacesBase


class CoffeeShopDensity(GooglePlacesBase):
    key = "coffee_shop_density"
    place_type = "cafe"
    search_radius = 200
    grid_max = 4.0
