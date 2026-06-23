from marshmallow import Schema, ValidationError, fields, pre_load, validates_schema
from marshmallow.validate import Length

from application.helpers import MAX_ITEM_DESCRIPTION_LENGTH, MAX_ITEM_NAME_LENGTH


class MessageSchema(Schema):
    message = fields.Str(required=True)


class HealthSchema(Schema):
    status = fields.Str(required=True)
    database = fields.Str(required=True)


class ErrorResponseSchema(Schema):
    error = fields.Str(required=True)


class ItemSchema(Schema):
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    created_at = fields.Str(allow_none=True, required=True)


class ItemListSchema(Schema):
    items = fields.List(fields.Nested(ItemSchema), required=True)


class ItemResponseSchema(Schema):
    item = fields.Nested(ItemSchema, required=True)


class DeleteResponseSchema(Schema):
    deleted = fields.Bool(required=True)
    id = fields.Str(required=True)


class ItemPayloadSchema(Schema):
    name = fields.Str(
        required=True,
        validate=Length(min=1, max=MAX_ITEM_NAME_LENGTH),
    )
    description = fields.Str(
        load_default='',
        validate=Length(max=MAX_ITEM_DESCRIPTION_LENGTH),
    )

    @pre_load
    def strip_text_fields(self, data, **kwargs):
        # 文字列の前後空白をバリデーション前に除去
        for field_name in ('name', 'description'):
            value = data.get(field_name)
            if isinstance(value, str):
                data[field_name] = value.strip()
        return data


class ItemPatchPayloadSchema(Schema):
    name = fields.Str(validate=Length(min=1, max=MAX_ITEM_NAME_LENGTH))
    description = fields.Str(validate=Length(max=MAX_ITEM_DESCRIPTION_LENGTH))

    @pre_load
    def strip_text_fields(self, data, **kwargs):
        # 文字列の前後空白をバリデーション前に除去
        for field_name in ('name', 'description'):
            value = data.get(field_name)
            if isinstance(value, str):
                data[field_name] = value.strip()
        return data

    @validates_schema
    def validate_has_update_field(self, data, **kwargs):
        # PATCH は少なくとも1つの更新対象フィールドを必須にする
        if not data:
            raise ValidationError('name or description is required')
