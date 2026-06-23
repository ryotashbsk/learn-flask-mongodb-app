# Flask + MongoDB

Flask から MongoDB の `items` collection を読み取る JSON API サンプル。

- フレームワーク: Flask
- DB クライアント: PyMongo
- WSGI サーバー: gunicorn
- Python 管理: uv
- ローカル DB: Docker Compose MongoDB

## ドキュメント

README が長くなりすぎないよう、詳細手順は目的別に `docs/` 配下へ分割しています。

| ドキュメント | 内容 |
| --- | --- |
| [セットアップ](docs/setup.md) | 前提ツール、Python 設定、ローカルセットアップ、MongoDB 初期データ |
| [API リファレンス](docs/api.md) | エンドポイント、Swagger UI、curl での動作確認 |
| [テストと品質チェック](docs/testing.md) | ty、pre-commit、pytest、coverage |
| [構成と運用メモ](docs/architecture.md) | ファイル構成、ロギング |

## クイックスタート

```bash
cp .env.example .env
uv venv --python 3.11
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
docker compose up -d mongo
uv run gunicorn app:app --bind 0.0.0.0:8080 --reload
```

## 主なエンドポイント

| メソッド | URL | 概要 |
| --- | --- | --- |
| GET | `http://localhost:8080/` | アプリのメッセージ |
| GET | `http://localhost:8080/health` | MongoDB への接続状態 |
| GET | `http://localhost:8080/items` | `items` collection のデータ |
| POST | `http://localhost:8080/items` | `items` collection へのデータ追加 |
| PUT | `http://localhost:8080/items/<id>` | `items` collection のデータ置換 |
| PATCH | `http://localhost:8080/items/<id>` | `items` collection のデータ部分更新 |
| DELETE | `http://localhost:8080/items/<id>` | `items` collection のデータ削除 |

API の詳細は [API リファレンス](docs/api.md) を参照してください。

## 品質チェック

```bash
uv run pre-commit run --all-files
```

個別の型チェック、テスト、カバレッジ計測は [テストと品質チェック](docs/testing.md) を参照してください。
