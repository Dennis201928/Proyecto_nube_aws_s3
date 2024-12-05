from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuración
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin123@cloud-meme-db.c1a0qycsqqme.us-east-2.rds.amazonaws.com:3306/cloud_meme_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

db = SQLAlchemy(app)
from dotenv import load_dotenv
load_dotenv()

# Validar la conexión a la base de datos
try:
    with app.app_context():
        # Intentar conexión
        db.session.execute('SELECT 1')
        print("Conexión a la base de datos exitosa.")
except Exception as e:
    print(f"Error al conectar con la base de datos: {e}")

# Importar rutas
from app import routes
