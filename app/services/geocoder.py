from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# Nominatim EXIGE un user_agent personalizado o bloquean tu IP.
geolocator = Nominatim(user_agent="siol_sava_tesis_geocoder")

def obtener_coordenadas(direccion: str):
    """
    Toma una dirección en texto y devuelve una tupla (Latitud, Longitud).
    """
    try:
        # IMPORTANTE: Nominatim es gratuito, pero exige máximo 1 petición por segundo.
        # Ponemos este 'sleep' para no saturar el servidor y evitar bloqueos.
        time.sleep(1)
        location = geolocator.geocode(direccion)
        
        if location:
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        return None, None
    except Exception as e:
        print(f"Error geocodificando {direccion}: {e}")
        return None, None