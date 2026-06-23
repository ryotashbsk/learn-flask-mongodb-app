# セットアップ

## 前提

| ツール | 用途 |
| --- | --- |
| uv | Python と仮想環境、依存パッケージの管理 |
| Docker Compose | ローカル MongoDB の起動 |
| MongoDB Compass | MongoDB のデータ確認 |
| Flask | Web API |
| flask-smorest | OpenAPI / Swagger UI、request / response schema |
| PyMongo | MongoDB 接続 |
| gunicorn | WSGI サーバー |
| Ruff | format / lint |
| ty | 型チェック |
| pytest | API 自動テスト |
| coverage | テストカバレッジ計測 |
| pre-commit | commit 前の品質チェック |

`Flask`、`flask-smorest`、`PyMongo`、`gunicorn` は `requirements.txt` で管理。  
`Ruff`、`ty`、`pytest`、`coverage`、`pre-commit` は `requirements-dev.txt` で管理。

## Python 設定

`pyproject.toml` は Ruff の lint / format と ty の型チェック設定ファイル。

| 設定 | 内容 |
| --- | --- |
| `tool.ruff.ignore` | このサンプルでの Ruff ルール無視対象 |
| `tool.ruff.format.quote-style` | 文字列引用符を single quote に統一 |
| `tool.ty.environment.python-version` | 型チェック対象の Python バージョン |
| `tool.ty.src.include` | 型チェック対象ファイル |
| `tool.pytest.ini_options.testpaths` | pytest のテスト対象ディレクトリ |
| `tool.coverage.run.source` | coverage の計測対象 |
| `tool.coverage.report` | coverage レポート表示設定 |

## ローカルセットアップ

ローカル実行用の環境変数ファイル。

```bash
cp .env.example .env
```

主な環境変数:

| 変数 | 内容 | 既定値 |
| --- | --- | --- |
| `MONGO_URI` | MongoDB 接続 URI | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | 使用する MongoDB database 名 | `sample_app` |
| `MONGO_TLS_CA_FILE` | TLS 接続時の CA ファイルパス | 未指定 |
| `LOG_LEVEL` | ログ出力レベル | `INFO` |

Python 3.11 の仮想環境。

```bash
uv venv --python 3.11
```

`.venv` への依存パッケージ追加。

```bash
uv pip install -r requirements.txt
```

開発用依存パッケージも含めて追加。

```bash
uv pip install -r requirements-dev.txt
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
