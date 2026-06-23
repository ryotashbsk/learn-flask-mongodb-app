from datetime import datetime

from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import jsonify

MAX_ITEM_NAME_LENGTH = 100
MAX_ITEM_DESCRIPTION_LENGTH = 1000


# MongoDB の item ドキュメントを JSON 返却用の dict に変換
def serialize_item(item: dict) -> dict:
    # ObjectId と datetime を JSON で扱える文字列に変換
    created_at = item.get('created_at')
    created_at_text = (
        created_at.isoformat() if isinstance(created_at, datetime) else None
    )

    return {
        'id': str(item['_id']),
        'name': item['name'],
        'description': item.get('description', ''),
        'created_at': created_at_text,
    }


# エラー内容と HTTP ステータスコードを JSON レスポンスとして返却
def error_response(message: str, status_code: int):
    # API のエラー形式を {"error": "..."} に統一
    return jsonify({'error': message}), status_code


# URL パラメータの文字列IDを MongoDB ObjectId に変換
def parse_item_id(item_id: str):
    try:
        # MongoDB の _id 検索で使える ObjectId に変換
        return ObjectId(item_id)
    except InvalidId:
        # ObjectId 形式ではないIDは呼び出し元で 400 として扱う
        return None
