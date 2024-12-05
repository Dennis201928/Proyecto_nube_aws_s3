import os
import boto3
from flask import request, jsonify, render_template
from app import app, db
from app.models import Etiqueta, Meme
from app.imagga import get_image_tags  # Importamos la función para obtener las etiquetas de Imagga

# Configuración del cliente S3
S3_BUCKET = "meme-storagee"  # Cambia por el nombre de tu bucket
S3_REGION = "us-east-2"
s3_client = boto3.client('s3', region_name=S3_REGION)

# Carpeta para subir archivos temporalmente
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return "<h1>¡Bienvenido a Cloud MemeDB!</h1>"

@app.route('/upload', methods=['POST'])
def upload_meme():
    try:
        # Verifica si el archivo está en la solicitud
        if 'file' not in request.files:
            return jsonify({"error": "No se encontró el campo 'file' en la solicitud"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400

        descripcion = request.form.get('descripcion', '')
        usuario = request.form.get('usuario', '')
        etiquetas = request.form.get('etiquetas', '')

        if not descripcion or not usuario or not etiquetas:
            return jsonify({"error": "Faltan campos requeridos"}), 400

        # Guardar temporalmente el archivo
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Subir el archivo a S3
        s3_client.upload_fileobj(
            open(file_path, 'rb'),
            S3_BUCKET,
            file.filename,
            ExtraArgs={"ContentType": file.content_type}
        )

        # Crear la URL del archivo subido
        ruta_s3 = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file.filename}"

        # Analizar la imagen con Imagga para obtener etiquetas
        tags_response = get_image_tags(file_path)  # Usamos la función que conecta con la API de Imagga
        if 'error' in tags_response:
            os.remove(file_path)  # Elimina el archivo temporal en caso de error
            return jsonify({"error": "Error al analizar la imagen", "details": tags_response['error']}), 500

        # Extraer las etiquetas generadas por Imagga
        tags = [tag['tag']['en'] for tag in tags_response['result']['tags'] if tag['confidence'] > 50]

        # Guardar el meme en la base de datos
        meme = Meme(descripcion=descripcion, ruta=ruta_s3, usuario=usuario)
        db.session.add(meme)
        db.session.commit()

        # Guardar las etiquetas en la base de datos
        for tag in tags:
            if not Etiqueta.query.filter_by(etiqueta=tag, meme_id=meme.id).first():
                nueva_etiqueta = Etiqueta(meme_id=meme.id, etiqueta=tag, confianza=0.75)  # Ajustar confianza
                db.session.add(nueva_etiqueta)

        db.session.commit()

        # Eliminar el archivo temporal
        os.remove(file_path)

        return jsonify({"message": "Meme cargado exitosamente", "ruta": ruta_s3, "tags": tags}), 200

    except Exception as e:
        # Captura y muestra el error
        print(f"Error durante la carga o análisis de la imagen: {str(e)}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500


@app.route('/search', methods=['GET'])
def search_meme():
    query = request.args.get('q', '')  # Obtiene el término de búsqueda
    if not query:
        return jsonify({"error": "Se necesita un término de búsqueda"}), 400

    # Quitar espacios adicionales y convertir el término a minúsculas
    query = query.strip().lower()

    # Buscar coincidencias parciales en la base de datos
    memes = Meme.query.filter(Meme.descripcion.ilike(f"%{query}%")).all()

    if not memes:
        return jsonify({"message": "No se encontraron resultados para la búsqueda"}), 404

    # Formatear los resultados
    resultados = [{"descripcion": meme.descripcion, "usuario": meme.usuario, "ruta": meme.ruta} for meme in memes]
    return jsonify(resultados), 200




@app.route('/form', methods=['GET'])
def upload_form():
    # Renderizar un formulario HTML para pruebas
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subir Meme</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 50px;
                text-align: center;
            }
            form {
                display: inline-block;
                text-align: left;
                margin-top: 20px;
            }
            input, button {
                display: block;
                margin: 10px 0;
                padding: 10px;
                font-size: 16px;
                width: 100%;
            }
            button {
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Subir Meme</h1>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <label for="file">Selecciona un archivo:</label>
            <input type="file" name="file" id="file" required>

            <label for="descripcion">Descripción:</label>
            <input type="text" name="descripcion" id="descripcion" placeholder="Describe el meme" required>

            <label for="usuario">Usuario:</label>
            <input type="text" name="usuario" id="usuario" placeholder="Tu nombre de usuario" required>

            <label for="etiquetas">Etiquetas (separadas por comas):</label>
            <input type="text" name="etiquetas" id="etiquetas" placeholder="Ejemplo: gracioso,humor,meme" required>

            <button type="submit">Subir Meme</button>
        </form>
    </body>
    </html>
    '''
