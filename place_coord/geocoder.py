import requests
from environs import Env
import traceback


env = Env()
env.read_env()


def fetch_coordinates(address, api_key=env('YANDEX_API_KEY')):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": api_key,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
        
        if not found_places:
            return None
        
        if 'error' in found_places:
            raise requests.exceptions.HTTPError(found_places['error'])
        
        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return float(lon), float(lat)
    
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка при запросе к геокодеру: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Ошибка при обработке ответа геокодера: {e}")
        return None
    