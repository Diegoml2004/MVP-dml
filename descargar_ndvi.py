import os
import requests
from dotenv import load_dotenv

# Cargar credenciales desde archivo .env
load_dotenv()
CLIENT_ID = os.getenv("SENTINEL_CLIENT_ID")
CLIENT_SECRET = os.getenv("SENTINEL_CLIENT_SECRET")
INSTANCE_ID = os.getenv("INSTANCE_ID")

# Autenticación OAuth2
def get_access_token(client_id, client_secret):
    url = "https://services.sentinel-hub.com/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["access_token"]

# Solicitar imagen NDVI
def descargar_ndvi(token, instance_id, coordenadas, tamaño_pixeles, nombre_archivo):
    url = f"https://services.sentinel-hub.com/ogc/wms/{instance_id}"

    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "LAYERS": "NDVI",
        "MAXCC": "20",
        "WIDTH": tamaño_pixeles,
        "HEIGHT": tamaño_pixeles,
        "BBOX": coordenadas,
        "FORMAT": "image/png",
        "CRS": "EPSG:4326",
        "TIME": "2025-07-20/2025-07-29",
        "SHOWLOGO": "false"
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    with open(nombre_archivo, "wb") as f:
        f.write(response.content)
    print(f"Imagen NDVI guardada como: {nombre_archivo}")

if __name__ == "__main__":
    token = get_access_token(CLIENT_ID, CLIENT_SECRET)

    # Coordenadas para una finca cerca de La Victoria, Manabí (Ecuador)
    bbox = "-1.75,-80.85,-1.65,-80.75"  # sur, oeste, norte, este
    descargar_ndvi(token, INSTANCE_ID, bbox, 512, "ndvi_map.png")
