from datetime import UTC, datetime

from flask import Flask, jsonify
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from application.helpers import (
    error_response,
    get_json_body,
    parse_item_id,
    read_item_payload,
    serialize_item,
)


def register_routes(
    app: Flask,
    mongo_client: MongoClient,
    items_collection: Collection,
) -> None:
    @app.errorhandler(413)
    def request_entity_too_large(error):
        # Flask の body サイズ制限超過を JSON 形式に統一
        return error_response('request body is too large', 413)

    # ------------------------------------
    # GET /
    # アプリケーションの疎通確認用メッセージ
    # ------------------------------------
    @app.get('/')
    def index():
        # アプリケーションが応答可能な状態かを固定メッセージで返却
        return {'message': 'Hello Flask + MongoDB'}

    # ------------------------------------
    # GET /health
    # MongoDB への接続状態確認
    # ------------------------------------
    @app.get('/health')
    def health():
        try:
            # MongoDB へ ping を送り、接続可能かを確認
            mongo_client.admin.command('ping')
            return {'status': 'ok', 'database': 'connected'}
        except PyMongoError as exc:
            # 接続エラーは 500 と詳細メッセージで返却
            return jsonify({'status': 'error', 'detail': str(exc)}), 500

    # ------------------------------------
    # GET /items
    # items collection の一覧取得
    # ------------------------------------
    @app.get('/items')
    def get_items():
        # name 昇順で collection の全 item を取得
        items = items_collection.find().sort('name', ASCENDING)
        # MongoDB 固有の型を JSON 返却用に変換
        return jsonify({'items': [serialize_item(item) for item in items]})

    # ------------------------------------
    # POST /items
    # items collection へのデータ追加
    # ------------------------------------
    @app.post('/items')
    def create_item():
        # JSON body の形式を検証
        body = get_json_body()
        if body is None:
            return error_response('JSON object body is required', 400)

        # 作成用 payload を検証して保存用 dict に変換
        item, item_error = read_item_payload(body, require_name=True)
        if item_error:
            return error_response(item_error, 400)

        # 新規作成日時を UTC で保存
        item['created_at'] = datetime.now(UTC)

        try:
            # item を collection に追加
            result = items_collection.insert_one(item)
        except DuplicateKeyError:
            # name の unique index 違反を 409 として返却
            return error_response('name already exists', 409)

        # 追加された ObjectId を返却用データに反映
        item['_id'] = result.inserted_id
        return jsonify({'item': serialize_item(item)}), 201

    # ------------------------------------
    # PUT /items/<item_id>
    # 指定IDの item 全体を置換
    # ------------------------------------
    @app.put('/items/<item_id>')
    def replace_item(item_id: str):
        # URL パラメータの ID 形式を検証
        object_id = parse_item_id(item_id)
        if object_id is None:
            return error_response('invalid item id', 400)

        # JSON body の形式を検証
        body = get_json_body()
        if body is None:
            return error_response('JSON object body is required', 400)

        # 置換用 payload を検証して保存用 dict に変換
        replacement, replacement_error = read_item_payload(body, require_name=True)
        if replacement_error:
            return error_response(replacement_error, 400)

        # 置換対象の存在確認
        current_item = items_collection.find_one({'_id': object_id})
        if current_item is None:
            return error_response('item not found', 404)

        # 作成日時は既存値を維持
        replacement['created_at'] = current_item.get('created_at') or datetime.now(UTC)

        try:
            # 指定IDの item を payload 全体で置換
            items_collection.replace_one({'_id': object_id}, replacement)
        except DuplicateKeyError:
            # name の unique index 違反を 409 として返却
            return error_response('name already exists', 409)

        # 置換後の ObjectId を返却用データに反映
        replacement['_id'] = object_id
        return jsonify({'item': serialize_item(replacement)})

    # ------------------------------------
    # PATCH /items/<item_id>
    # 指定IDの item を部分更新
    # ------------------------------------
    @app.patch('/items/<item_id>')
    def update_item(item_id: str):
        # URL パラメータの ID 形式を検証
        object_id = parse_item_id(item_id)
        if object_id is None:
            return error_response('invalid item id', 400)

        # JSON body の形式を検証
        body = get_json_body()
        if body is None:
            return error_response('JSON object body is required', 400)

        # 部分更新用 payload を検証して $set 用 dict に変換
        update_fields, update_error = read_item_payload(body, require_name=False)
        if update_error:
            return error_response(update_error, 400)

        try:
            # 指定IDの item に指定フィールドのみ反映
            result = items_collection.update_one(
                {'_id': object_id},
                {'$set': update_fields},
            )
        except DuplicateKeyError:
            # name の unique index 違反を 409 として返却
            return error_response('name already exists', 409)

        # 更新対象が存在しない場合は 404
        if result.matched_count == 0:
            return error_response('item not found', 404)

        # 更新後の item を再取得して返却
        updated_item = items_collection.find_one({'_id': object_id})
        return jsonify({'item': serialize_item(updated_item)})

    # ------------------------------------
    # DELETE /items/<item_id>
    # 指定IDの item を削除
    # ------------------------------------
    @app.delete('/items/<item_id>')
    def delete_item(item_id: str):
        # URL パラメータの ID 形式を検証
        object_id = parse_item_id(item_id)
        if object_id is None:
            return error_response('invalid item id', 400)

        # 指定IDの item を削除
        result = items_collection.delete_one({'_id': object_id})
        if result.deleted_count == 0:
            return error_response('item not found', 404)

        # 削除成功時は対象IDを返却
        return jsonify({'deleted': True, 'id': item_id})
