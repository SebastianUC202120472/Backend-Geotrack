import math

def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Fórmula de Haversine para calcular distancia en KM entre dos puntos.
    """
    R = 6371.0 # Radio de la Tierra en km
    
    # Convertir a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distancia = R * c
    return distancia

def optimizar_secuencia_pedidos(pedidos, lat_origen, lon_origen):
    """
    Algoritmo del 'Vecino Más Cercano' (Greedy) REFORZADO.
    Garantiza procesar todos los pedidos de la lista.
    """
    pedidos_pendientes = pedidos.copy()
    ruta_optima = []
    
    punto_actual = (lat_origen, lon_origen)
    
    # Bucle de seguridad para evitar ciclos infinitos
    intentos = len(pedidos_pendientes) * 2 
    
    while pedidos_pendientes and intentos > 0:
        intentos -= 1
        
        pedido_mas_cercano = None
        distancia_minima = float('inf')
        
        for pedido in pedidos_pendientes:
            # Validación extra de seguridad
            if pedido.latitud is None or pedido.longitud is None:
                continue
                
            distancia = calcular_distancia(
                punto_actual[0], punto_actual[1], 
                pedido.latitud, pedido.longitud
            )
            
            # Usamos <= para manejar el caso donde dos pedidos tienen EXACTAMENTE
            # las mismas coordenadas (distancia 0)
            if distancia <= distancia_minima:
                distancia_minima = distancia
                pedido_mas_cercano = pedido
        
        if pedido_mas_cercano:
            ruta_optima.append(pedido_mas_cercano)
            pedidos_pendientes.remove(pedido_mas_cercano)
            punto_actual = (pedido_mas_cercano.latitud, pedido_mas_cercano.longitud)
        else:
            # Si no encontró ninguno (ej. todos los restantes no tenían coordenadas)
            # los añade al final sin optimizar para no perder la carga.
            ruta_optima.extend(pedidos_pendientes)
            break
            
    return ruta_optima