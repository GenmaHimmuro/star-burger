from place_coord.models import Place
from place_coord.geocoder import fetch_coordinates


def get_all_coordinates(all_addresses):
    addresses_set = set(all_addresses)
    places = Place.objects.filter(address__in=addresses_set)

    coords_map = {
        p.address: (p.lat, p.lon)
        for p in places
        if p.lat is not None and p.lon is not None
    }
    missing = addresses_set - coords_map.keys()

    for address in missing:
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
