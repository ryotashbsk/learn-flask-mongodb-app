import os

from dotenv import load_dotenv
from flask import Flask
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
register_routes(app, mongo_client, items_collection)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
