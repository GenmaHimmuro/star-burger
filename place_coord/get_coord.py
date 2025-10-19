from place_coord.models import Place
from place_coord.geocoder import fetch_coordinates


def get_all_coordinates(order_addresses, restaurant_addresses):
    all_addresses = set(order_addresses) | set(restaurant_addresses)
    places = Place.objects.filter(address__in=all_addresses)
    coords_map = {place.address: (place.lat, place.lon) for place in places if place.lat and place.lon}
    missing_addresses = all_addresses - set(coords_map.keys())

    for address in missing_addresses:
        coords = fetch_coordinates(address)
        if coords:
            lon, lat = coords
            Place.objects.update_or_create(
                address=address,
                defaults={'lat': lat, 'lon': lon}
            )
            coords_map[address] = (lat, lon)
        else:
            coords_map[address] = None
    return coords_map
