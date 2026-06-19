import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'sample_app')
MONGO_TLS_CA_FILE = os.getenv('MONGO_TLS_CA_FILE')

client_kwargs = {}
if MONGO_TLS_CA_FILE:
    client_kwargs['tls'] = True
    client_kwargs['tlsCAFile'] = MONGO_TLS_CA_FILE

mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, **client_kwargs)
db = mongo_client[MONGO_DB_NAME]
items_collection = db['items']

app = Flask(__name__)


def serialize_item(item: dict) -> dict:
    return {
        'id': str(item['_id']),
        'name': item['name'],
        'description': item.get('description', ''),
        'created_at': item.get('created_at').isoformat()
        if item.get('created_at')
        else None,
    }


@app.get('/')
def index():
    return {'message': 'Hello Flask + MongoDB'}


@app.get('/health')
def health():
    try:
        mongo_client.admin.command('ping')
        return {'status': 'ok', 'database': 'connected'}
    except PyMongoError as exc:
        return jsonify({'status': 'error', 'detail': str(exc)}), 500


@app.get('/items')
def get_items():
    items = items_collection.find().sort('name', ASCENDING)
    return jsonify({'items': [serialize_item(item) for item in items]})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
