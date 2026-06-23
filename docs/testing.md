# テストと品質チェック

## 型チェック

ty による型チェック。

```bash
uv run ty check
```

## pre-commit

commit 前に品質チェックを自動実行する。

初回のみ Git hook をインストール。

```bash
uv run pre-commit install
```

以後、通常の `git commit` や GUI からの commit 時に `.pre-commit-config.yaml` の hook が実行される。

実行内容:

| hook | 内容 |
| --- | --- |
| `ruff format --check .` | format 未適用の検出 |
| `ruff check .` | lint |
| `ty check` | 型チェック |
| `pytest` | API 自動テスト |

全hookを手動実行。

```bash
uv run pre-commit run --all-files
```

## 自動テスト

pytest による API 自動テスト。

```bash
uv run pytest
```

pytest は `pyproject.toml` の `tool.pytest.ini_options.testpaths` により、`tests/` ディレクトリをテスト対象として読み込む。

| ファイル | 役割 |
| --- | --- |
| `tests/conftest.py` | テスト実行時にプロジェクトルートを import path に追加 |
| `tests/test_api.py` | Flask の `test_client()` を使った API テスト |

`tests/test_api.py` では、実際の MongoDB には接続しない。  
`FakeMongoClient` と `FakeItemsCollection` を使って、テスト用の Flask アプリに `register_routes()` を登録する。

テスト対象:

| 対象 | 内容 |
| --- | --- |
| 疎通確認 | `GET /` |
| ヘルスチェック | `GET /health` |
| CRUD | `GET /items`、`POST /items`、`PUT /items/<id>`、`PATCH /items/<id>`、`DELETE /items/<id>` |
| エラー系 | 不正ID、重複 `name`、不正 payload、存在しない item |
| API ドキュメント | `/docs/openapi.json`、`/docs/swagger-ui` |

テストの流れ:

```txt
uv run pytest
  ↓
tests/ 配下の test_*.py を収集
  ↓
fixture でテスト用 Flask アプリを作成
  ↓
test_client() で API を呼び出し
  ↓
assert でステータスコードと JSON を検証
```

### テストの書き方

テストファイルは `tests/test_*.py` として作成する。  
テスト関数は `test_` で始める。

```python
def test_index(client):
    response = client.get('/')

    assert response.status_code == 200
    assert response.get_json() == {'message': 'Hello Flask + MongoDB'}
```

`client` は pytest の fixture。  
テスト関数の引数に `client` と書くと、pytest が自動でテスト用 Flask アプリの `test_client()` を渡す。

API のテストでは、基本的に以下を確認する。

| 確認対象 | 例 |
| --- | --- |
| HTTP ステータス | `assert response.status_code == 200` |
| レスポンス JSON | `assert response.get_json()['item']['name'] == 'Orange'` |
| エラー内容 | `assert response.get_json() == {'error': 'item not found'}` |
| 状態変化 | `POST` 後に作成結果を確認、`DELETE` 後に削除結果を確認 |

POST / PUT / PATCH は `json=` に送信 payload を渡す。

```python
def test_create_item(client):
    response = client.post(
        '/items',
        json={'name': 'Orange', 'description': 'Created by POST'},
    )

    assert response.status_code == 201
    assert response.get_json()['item']['name'] == 'Orange'
```

異常系も正常系と同じ形式で書く。

```python
def test_replace_item_rejects_invalid_id(client):
    response = client.put('/items/invalid-id', json={'name': 'Grape'})

    assert response.status_code == 400
    assert response.get_json() == {'error': 'invalid item id'}
```

新しいエンドポイントを追加した場合は、最低限以下を追加する。

| 種類 | 内容 |
| --- | --- |
| 正常系 | 期待するステータスコードと JSON |
| 入力エラー | 不正 payload や不正ID |
| 対象なし | 存在しないIDに対する 404 |
| ドキュメント | OpenAPI JSON に path が含まれること |

## カバレッジ

coverage によるテスト実行行の計測。

```bash
uv run coverage run -m pytest
uv run coverage report
```

HTML レポートを生成。

```bash
uv run coverage html
```

HTML は `htmlcov/index.html` で確認。

`coverage report` の見方:

| 列 | 内容 |
| --- | --- |
| `Stmts` | 計測対象の実行可能な行数 |
| `Miss` | テストで実行されなかった行数 |
| `Cover` | 実行された行の割合 |
| `Missing` | 実行されなかった行番号 |

カバレッジは数値を上げること自体が目的ではない。  
未対応行を見て、重要な仕様や壊れやすい分岐がテストされているかを確認する。

テスト追加を優先する例:

| 優先度 | 内容 |
| --- | --- |
| 高 | APIのレスポンスが変わる分岐 |
| 高 | `400`、`404`、`409`、`500` などのエラー分岐 |
| 高 | DB操作の成功・失敗・対象なし |
| 中 | body サイズ超過や schema バリデーション |
| 低 | 実装詳細に強く依存するだけの分岐 |

判断基準:

```txt
この分岐が壊れたとき、利用者に影響があるか
この分岐は今後の変更で壊れやすいか
README や OpenAPI に書いている仕様か
テストが不自然な実装詳細に依存しないか
```

目安として、最初から100%を目指さない。  
正常系、主要な異常系、DB操作の結果判定、公開APIのレスポンス仕様を優先して埋める。
