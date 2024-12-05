import requests
import os
import requests

# Configura tus credenciales de Imagga
IMAGGA_API_KEY = 'acc_0c2aa3a2bad0abd'
IMAGGA_API_SECRET = 'd6038f2ccf5b1a2db5df45f55fbbf1e8'
IMAGGA_ENDPOINT = 'https://api.imagga.com/v2/tags'

def get_image_tags(image_path):
    # Abre el archivo como un stream y no lo cierra automáticamente
    try:
        with open(image_path, 'rb') as image_file:
            response = requests.post(
                IMAGGA_ENDPOINT,
                auth=(IMAGGA_API_KEY, IMAGGA_API_SECRET),
                files={'image': image_file}
            )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except Exception as e:
        return {"error": f"Error al procesar la imagen: {str(e)}"}

