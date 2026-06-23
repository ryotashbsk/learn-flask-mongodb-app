from datetime import datetime

from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import jsonify, request

ALLOWED_ITEM_FIELDS = {'name', 'description'}
MAX_ITEM_NAME_LENGTH = 100
MAX_ITEM_DESCRIPTION_LENGTH = 1000


# MongoDB の item ドキュメントを JSON 返却用の dict に変換
def serialize_item(item: dict) -> dict:
    # ObjectId と datetime を JSON で扱える文字列に変換
    created_at = item.get('created_at')
    created_at_text = created_at.isoformat() if isinstance(created_at, datetime) else None

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


# リクエストボディを JSON object として取得
def get_json_body():
    # Content-Type が JSON 以外の場合は不正な body として扱う
    if not request.is_json:
        return None

    # JSON パース失敗時も例外ではなく None として扱う
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None

    return body


# URL パラメータの文字列IDを MongoDB ObjectId に変換
def parse_item_id(item_id: str):
    try:
        # MongoDB の _id 検索で使える ObjectId に変換
        return ObjectId(item_id)
    except InvalidId:
        # ObjectId 形式ではないIDは呼び出し元で 400 として扱う
        return None


# JSON body から文字列フィールドを取得して必須チェック
def read_text_field(
    body: dict,
    field_name: str,
    *,
    required: bool,
    max_length: int,
):
    # 対象フィールドの値を JSON body から取得
    value = body.get(field_name)

    # 必須項目が未指定の場合だけエラー
    if value is None:
        if required:
            return None, f'{field_name} is required'
        return '', None

    # API で受け付ける値を文字列に限定
    if not isinstance(value, str):
        return None, f'{field_name} must be a string'

    # 前後の空白を保存対象から除外
    value = value.strip()
    if required and not value:
        return None, f'{field_name} is required'

    # 想定外に大きい値を保存前に拒否
    if len(value) > max_length:
        return None, f'{field_name} must be {max_length} characters or less'

    return value, None


# item 作成・更新用の JSON body を検証して保存用 dict に変換
def read_item_payload(body: dict, *, require_name: bool):
    # 保存対象外のフィールドを明示的に拒否
    unknown_fields = sorted(set(body) - ALLOWED_ITEM_FIELDS)
    if unknown_fields:
        return None, f'unknown fields: {", ".join(unknown_fields)}'

    # 検証済みの値だけを保存用 dict に詰める
    item = {}
    if require_name or 'name' in body:
        # 作成・置換では name 必須、部分更新では指定時のみ検証
        name, name_error = read_text_field(
            body,
            'name',
            required=True,
            max_length=MAX_ITEM_NAME_LENGTH,
        )
        if name_error:
            return None, name_error
        item['name'] = name

    if require_name or 'description' in body:
        # description は任意項目として検証
        description, description_error = read_text_field(
            body,
            'description',
            required=False,
            max_length=MAX_ITEM_DESCRIPTION_LENGTH,
        )
        if description_error:
            return None, description_error
        item['description'] = description

    if not item:
        # 部分更新で更新対象フィールドがない場合はエラー
        return None, 'name or description is required'

    return item, None
