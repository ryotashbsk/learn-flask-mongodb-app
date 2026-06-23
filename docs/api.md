# API リファレンス

## エンドポイント

| メソッド | URL | 概要 |
| --- | --- | --- |
| GET | `http://localhost:8080/` | アプリのメッセージ |
| GET | `http://localhost:8080/health` | MongoDB への接続状態 |
| GET | `http://localhost:8080/items` | `items` collection のデータ |
| POST | `http://localhost:8080/items` | `items` collection へのデータ追加 |
| PUT | `http://localhost:8080/items/<id>` | `items` collection のデータ置換 |
| PATCH | `http://localhost:8080/items/<id>` | `items` collection のデータ部分更新 |
| DELETE | `http://localhost:8080/items/<id>` | `items` collection のデータ削除 |

## API ドキュメント

| メソッド | URL | 概要 |
| --- | --- | --- |
| GET | `http://localhost:8080/docs/swagger-ui` | Swagger UI |
| GET | `http://localhost:8080/docs/openapi.json` | OpenAPI JSON |

## 動作確認

MongoDB への接続状態。

```bash
curl http://localhost:8080/health
```

`items` collection のデータ。

```bash
curl http://localhost:8080/items
```

返却例:

```json
{
  "items": [
    {
      "id": "...",
      "name": "Apple",
      "description": "Flask sample item from MongoDB",
      "created_at": "2026-01-01T00:00:00"
    }
  ]
}
```

`items` collection へのデータ追加。

```bash
curl -X POST http://localhost:8080/items \
  -H 'Content-Type: application/json' \
  -d '{"name":"Orange","description":"Created by POST"}'
```

```json
{
  "item": {
    "id": "...",
    "name": "Orange",
    "description": "Created by POST",
    "created_at": "2026-06-22T00:00:00.000000+00:00"
  }
}
```

`items` collection のデータ置換。

```bash
curl -X PUT http://localhost:8080/items/<id> \
  -H 'Content-Type: application/json' \
  -d '{"name":"Orange","description":"Replaced by PUT"}'
```

`items` collection のデータ部分更新。

```bash
curl -X PATCH http://localhost:8080/items/<id> \
  -H 'Content-Type: application/json' \
  -d '{"description":"Updated by PATCH"}'
```

`items` collection のデータ削除。

```bash
curl -X DELETE http://localhost:8080/items/<id>
```
