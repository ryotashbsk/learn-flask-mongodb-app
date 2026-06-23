import os

from dotenv import load_dotenv
from flask import Flask
from flask_smorest import Api
from pymongo import MongoClient

from application.routes import register_routes

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'sample_app')
MONGO_TLS_CA_FILE = os.getenv('MONGO_TLS_CA_FILE')

if MONGO_TLS_CA_FILE:
    mongo_client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        tls=True,
        tlsCAFile=MONGO_TLS_CA_FILE,
    )
else:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

db = mongo_client[MONGO_DB_NAME]
items_collection = db['items']

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
app.config['API_TITLE'] = 'Flask MongoDB API'
app.config['API_VERSION'] = '1.0.0'
app.config['OPENAPI_VERSION'] = '3.0.3'
app.config['OPENAPI_URL_PREFIX'] = '/docs'
app.config['OPENAPI_JSON_PATH'] = 'openapi.json'
app.config['OPENAPI_SWAGGER_UI_PATH'] = '/swagger-ui'
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

api = Api(app)
register_routes(app, api, mongo_client, items_collection)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
