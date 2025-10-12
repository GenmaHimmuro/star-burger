from place_coord.models import Place
from geocoder import fetch_coordinates


def get_address_coords(address):
    place, _ = Place.objects.get_or_create(address=address)
    if place.lat and place.lon:
        return (place.lat, place.lon)
    coords = fetch_coordinates(address)
    if coords:
        lon, lat = coords
        place.lat, place.lon = lat, lon
        place.save()
        return (lat, lon)
    return None


def get_restaurant_coords(restaurant):
    place, _ = Place.objects.get_or_create(address=restaurant.address)
    if place.lat and place.lon:
        return (place.lat, place.lon)
    coords = fetch_coordinates(restaurant.address)
    if coords:
        lon, lat = coords
        place.lat, place.lon = lat, lon
        place.save()
        return (lat, lon)
    return None
