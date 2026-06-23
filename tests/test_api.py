from datetime import UTC, datetime

import pytest
from bson.objectid import ObjectId
from flask import Flask
from flask_smorest import Api
from pymongo.errors import DuplicateKeyError, PyMongoError

from application.routes import register_routes


class FakeAdmin:
    def __init__(self):
        self.should_fail = False

    def command(self, name: str):
        if self.should_fail:
            raise PyMongoError('ping failed')
        return {'ok': 1, 'command': name}


class FakeMongoClient:
    def __init__(self):
        self.admin = FakeAdmin()


class FakeInsertResult:
    def __init__(self, inserted_id: ObjectId):
        self.inserted_id = inserted_id


class FakeUpdateResult:
    def __init__(self, matched_count: int):
        self.matched_count = matched_count


class FakeDeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class FakeCursor:
    def __init__(self, items: list[dict]):
        self.items = items

    def sort(self, field_name: str, direction: int):
        return sorted(self.items, key=lambda item: item[field_name])


class FakeItemsCollection:
    def __init__(self):
        self.items = [
            {
                '_id': ObjectId('000000000000000000000001'),
                'name': 'Apple',
                'description': 'Initial apple',
                'created_at': datetime(2026, 1, 1, tzinfo=UTC),
            },
            {
                '_id': ObjectId('000000000000000000000002'),
                'name': 'Banana',
                'description': 'Initial banana',
                'created_at': datetime(2026, 1, 2, tzinfo=UTC),
            },
        ]

    def find(self):
        return FakeCursor(self.items)

    def find_one(self, query: dict):
        object_id = query['_id']
        return next((item for item in self.items if item['_id'] == object_id), None)

    def insert_one(self, item: dict):
        if self._has_name(item['name']):
            raise DuplicateKeyError('duplicate name')

        inserted_id = ObjectId()
        item['_id'] = inserted_id
        self.items.append(item.copy())
        return FakeInsertResult(inserted_id)

    def replace_one(self, query: dict, replacement: dict):
        object_id = query['_id']
        if self._has_name(replacement['name'], exclude_id=object_id):
            raise DuplicateKeyError('duplicate name')

        for index, item in enumerate(self.items):
            if item['_id'] == object_id:
                next_item = replacement.copy()
                next_item['_id'] = object_id
                self.items[index] = next_item
                return FakeUpdateResult(1)

        return FakeUpdateResult(0)

    def update_one(self, query: dict, update: dict):
        object_id = query['_id']
        update_fields = update['$set']
        if 'name' in update_fields and self._has_name(
            update_fields['name'],
            exclude_id=object_id,
        ):
            raise DuplicateKeyError('duplicate name')

        item = self.find_one({'_id': object_id})
        if item is None:
            return FakeUpdateResult(0)

        item.update(update_fields)
        return FakeUpdateResult(1)

    def delete_one(self, query: dict):
        object_id = query['_id']
        for index, item in enumerate(self.items):
            if item['_id'] == object_id:
                del self.items[index]
                return FakeDeleteResult(1)

        return FakeDeleteResult(0)

    def _has_name(self, name: str, *, exclude_id: ObjectId | None = None) -> bool:
        return any(
            item['name'] == name and item['_id'] != exclude_id for item in self.items
        )


@pytest.fixture
def fake_collection():
    return FakeItemsCollection()


@pytest.fixture
def fake_mongo_client():
    return FakeMongoClient()


@pytest.fixture
def client(fake_collection, fake_mongo_client):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
    app.config['API_TITLE'] = 'Test API'
    app.config['API_VERSION'] = '1.0.0'
    app.config['OPENAPI_VERSION'] = '3.0.3'
    app.config['OPENAPI_URL_PREFIX'] = '/docs'
    app.config['OPENAPI_JSON_PATH'] = 'openapi.json'
    app.config['OPENAPI_SWAGGER_UI_PATH'] = '/swagger-ui'
    app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

    api = Api(app)
    register_routes(app, api, fake_mongo_client, fake_collection)

    return app.test_client()


def test_index(client):
    response = client.get('/')

    assert response.status_code == 200
    assert response.get_json() == {'message': 'Hello Flask + MongoDB'}


def test_health(client):
    response = client.get('/health')

    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok', 'database': 'connected'}


def test_health_error(client, fake_mongo_client):
    fake_mongo_client.admin.should_fail = True

    response = client.get('/health')

    assert response.status_code == 500
    assert response.get_json() == {'status': 'error', 'detail': 'ping failed'}


def test_get_items(client):
    response = client.get('/items')

    assert response.status_code == 200
    assert [item['name'] for item in response.get_json()['items']] == [
        'Apple',
        'Banana',
    ]


def test_create_item(client):
    response = client.post(
        '/items',
        json={'name': 'Orange', 'description': 'Created by POST'},
    )

    assert response.status_code == 201
    assert response.get_json()['item']['name'] == 'Orange'
    assert response.get_json()['item']['description'] == 'Created by POST'


def test_create_item_rejects_duplicate_name(client):
    response = client.post('/items', json={'name': 'Apple'})

    assert response.status_code == 409
    assert response.get_json() == {'error': 'name already exists'}


def test_create_item_rejects_invalid_payload(client):
    response = client.post('/items', json={'name': '', 'extra': 'x'})

    assert response.status_code == 422
    errors = response.get_json()['errors']['json']
    assert 'extra' in errors
    assert 'name' in errors


def test_replace_item(client):
    response = client.put(
        '/items/000000000000000000000001',
        json={'name': 'Grape', 'description': 'Replaced by PUT'},
    )

    assert response.status_code == 200
    assert response.get_json()['item']['id'] == '000000000000000000000001'
    assert response.get_json()['item']['name'] == 'Grape'
    assert response.get_json()['item']['description'] == 'Replaced by PUT'


def test_replace_item_rejects_invalid_id(client):
    response = client.put('/items/invalid-id', json={'name': 'Grape'})

    assert response.status_code == 400
    assert response.get_json() == {'error': 'invalid item id'}


def test_update_item(client):
    response = client.patch(
        '/items/000000000000000000000001',
        json={'description': 'Updated by PATCH'},
    )

    assert response.status_code == 200
    assert response.get_json()['item']['name'] == 'Apple'
    assert response.get_json()['item']['description'] == 'Updated by PATCH'


def test_update_item_rejects_empty_payload(client):
    response = client.patch('/items/000000000000000000000001', json={})

    assert response.status_code == 422
    assert response.get_json()['errors']['json']['_schema'] == [
        'name or description is required'
    ]


def test_delete_item(client):
    response = client.delete('/items/000000000000000000000001')

    assert response.status_code == 200
    assert response.get_json() == {
        'deleted': True,
        'id': '000000000000000000000001',
    }


def test_delete_item_returns_404(client):
    response = client.delete('/items/000000000000000000000099')

    assert response.status_code == 404
    assert response.get_json() == {'error': 'item not found'}


def test_openapi_json(client):
    response = client.get('/docs/openapi.json')

    assert response.status_code == 200
    assert sorted(response.get_json()['paths']) == [
        '/',
        '/health',
        '/items',
        '/items/{item_id}',
    ]


def test_swagger_ui(client):
    response = client.get('/docs/swagger-ui')

    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
