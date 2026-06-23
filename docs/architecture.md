# 構成と運用メモ

## ファイル構成

```txt
learn-flask-mongodb-app/
├── app.py
├── application/
│   ├── __init__.py
│   ├── helpers.py
│   ├── routes.py
│   └── schemas.py
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── setup.md
│   └── testing.md
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .editorconfig
├── .pre-commit-config.yaml
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

## ロギング

標準ライブラリの `logging` でアプリケーションログを出力する。  
ログレベルは `.env` の `LOG_LEVEL` で変更できる。

```txt
LOG_LEVEL=DEBUG
```

ログに出す内容:

| 種類 | 内容 |
| --- | --- |
| 起動時 | database 名、ログレベル |
| ヘルスチェック | MongoDB 接続失敗 |
| 一覧取得 | 取得件数、`DEBUG` レベル |
| 作成・置換・更新・削除 | 対象 item ID |
| エラー系 | 不正ID、重複 `name`、対象なし、body サイズ超過 |

リクエスト本文や secret はログに出さない。
