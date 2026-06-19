# Flask + MongoDB

Flask から MongoDB の `items` collection を読み取る JSON API サンプル。

- フレームワーク: Flask
- DB クライアント: PyMongo
- WSGI サーバー: gunicorn
- Python 管理: uv
- ローカル DB: Docker Compose MongoDB

## 前提

| ツール | 用途 |
| --- | --- |
| uv | Python と仮想環境、依存パッケージの管理 |
| Docker Compose | ローカル MongoDB の起動 |
| MongoDB Compass | MongoDB のデータ確認 |

## ファイル構成

```txt
flask-app/
├── app.py
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
├── mongo-init/
│   └── 001-items.js
├── .vscode/
│   ├── launch.json
│   └── settings.json
├── .env.example
├── Dockerfile
└── README.md
```

## エンドポイント

| メソッド | URL | 概要 |
| --- | --- | --- |
| GET | `http://localhost:8080/` | アプリのメッセージ |
| GET | `http://localhost:8080/health` | MongoDB への接続状態 |
| GET | `http://localhost:8080/items` | `items` collection のデータ |

## Python 設定

`pyproject.toml` は Ruff の lint / format 設定ファイル。

| 設定 | 内容 |
| --- | --- |
| `tool.ruff.ignore` | このサンプルでの Ruff ルール無視対象 |
| `tool.ruff.format.quote-style` | 文字列引用符を single quote に統一 |

## ローカルセットアップ

ローカル実行用の環境変数ファイル。

```bash
cp .env.example .env
```

Python 3.11 の仮想環境。

```bash
uv venv --python 3.11
```

`.venv` への依存パッケージ追加。

```bash
uv pip install -r requirements.txt
```

MongoDB コンテナのバックグラウンド起動。

```bash
docker compose up -d mongo
```

gunicorn による Flask アプリ起動。

```bash
uv run gunicorn app:app --bind 0.0.0.0:8080 --reload
```

VS Code では、実行とデバッグの `Flask アプリを起動` を利用。

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

## ローカル MongoDB

アプリが使う接続情報:

```txt
URI: mongodb://localhost:27017
DB: sample_app
Collection: items
```

MongoDB Compass の接続 URI:

```txt
mongodb://localhost:27017
```

## 初期データ

初期データの定義場所は `mongo-init/001-items.js`。  
MongoDB 公式イメージの `/docker-entrypoint-initdb.d` へのマウントにより、`mongo-data` volume が空の初回起動時だけ実行。

既存の `mongo-data` volume がある場合、初期データファイルは自動再実行なし。  
再初期化時は volume 削除後に起動。

```bash
docker compose down -v
docker compose up -d mongo
```
