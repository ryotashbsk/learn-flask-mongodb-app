# AWS App Runner デプロイ手順

このアプリを AWS App Runner で動かすためのメモです。App Runner は GitHub/Bitbucket のソースコード、または ECR のコンテナイメージからサービスを作成できます。このリポジトリでは、まず試しやすい **ソースコードリポジトリ方式**を主な手順にしています。

> 注意: AWS 公式ドキュメントでは、App Runner は新規顧客への提供が停止され、既存顧客は通常どおり利用可能と案内されています。新しい AWS アカウントで検証する場合は、コンソールで App Runner を利用できるか先に確認してください。

## 追加済みの設定ファイル

| ファイル | 用途 |
| --- | --- |
| `apprunner.yaml` | App Runner がソースコードをビルドし、gunicorn で Flask アプリを起動するための設定 |
| `aws/apprunner-source-service.example.json` | `aws apprunner create-service` 用の入力 JSON テンプレート |
| `aws/apprunner-instance-role-policy.example.json` | Secrets Manager / SSM Parameter Store から `MONGO_URI` を読むためのインスタンスロール用 IAM ポリシー例 |
| `.dockerignore` | ECR イメージ方式を試す場合に不要なローカルファイルを Docker build context から除外 |

## 前提

- App Runner が利用可能な AWS アカウントとリージョン
- AWS CLI v2 が設定済み
- App Runner から接続できる MongoDB
  - 例: MongoDB Atlas のパブリックエンドポイント
  - VPC 内 MongoDB に接続する場合は App Runner の VPC Connector 設定が別途必要
- GitHub などに push 済みのこのリポジトリ

## 環境変数

| 名前 | 必須 | 例 | 説明 |
| --- | --- | --- | --- |
| `MONGO_URI` | 必須 | `mongodb+srv://user:password@example.mongodb.net/?retryWrites=true&w=majority` | MongoDB 接続文字列。機密情報のため Secrets Manager または SSM Parameter Store 推奨 |
| `MONGO_DB_NAME` | 任意 | `sample_app` | 利用する MongoDB database 名 |
| `LOG_LEVEL` | 任意 | `INFO` | Python logging のログレベル |

`PORT` は App Runner が利用する予約済みの環境変数です。アプリ側では `apprunner.yaml` の `run.network.port` と gunicorn の bind を `8080` にそろえています。

## AWS Console からデプロイする

1. このリポジトリを GitHub に push します。
2. AWS Console で App Runner を開き、対象リージョンを選びます。
3. **Create service** を選択します。
4. Source は **Source code repository** を選びます。
5. GitHub 接続を未作成の場合は **Add new** で接続を作成し、このリポジトリへのアクセスを許可します。
6. Repository と Branch を選択します。
7. Deployment settings は検証用途なら **Automatic** を選ぶと、対象 branch への push 後に自動デプロイされます。
8. Configure build は **Use a configuration file** を選び、リポジトリルートの `apprunner.yaml` を使います。
9. Service settings で以下を設定します。
   - Service name: `learn-flask-mongodb-app` など
   - Port: `8080`（`apprunner.yaml` と一致）
   - CPU / Memory: 検証用途は `1 vCPU` / `2 GB` 程度
   - Environment variables:
     - `MONGO_DB_NAME=sample_app`
     - `LOG_LEVEL=INFO`
     - `MONGO_URI` は Plain text ではなく、Secrets Manager または SSM Parameter Store 参照を推奨
10. `MONGO_URI` を Secrets Manager / SSM Parameter Store 参照にする場合は、App Runner の Instance role に読み取り権限を付与します。ポリシー例は `aws/apprunner-instance-role-policy.example.json` を参照してください。
11. Health check は HTTP path `/health` を指定します。
12. Review して **Create & deploy** を実行します。
13. デプロイ完了後、App Runner の default domain で以下を確認します。

```bash
curl https://YOUR_SERVICE_URL/
curl https://YOUR_SERVICE_URL/health
curl https://YOUR_SERVICE_URL/items
```

## AWS CLI からデプロイする

### 1. MongoDB 接続文字列を Secrets Manager に保存する

```bash
aws secretsmanager create-secret \
  --region ap-northeast-1 \
  --name learn-flask-mongodb-app/mongo-uri \
  --secret-string 'mongodb+srv://USER:PASSWORD@example.mongodb.net/?retryWrites=true&w=majority'
```

SSM Parameter Store を使う場合は、SecureString として保存します。

```bash
aws ssm put-parameter \
  --region ap-northeast-1 \
  --name /learn-flask-mongodb-app/mongo-uri \
  --type SecureString \
  --value 'mongodb+srv://USER:PASSWORD@example.mongodb.net/?retryWrites=true&w=majority'
```

### 2. App Runner 用の GitHub connection を作成する

CLI で connection を作成すると、戻り値の `ConnectionArn` を使えます。GitHub 側の認可はコンソールで完了させる必要があります。

```bash
aws apprunner create-connection \
  --region ap-northeast-1 \
  --connection-name github-connection \
  --provider-type GITHUB
```

### 3. Instance role を用意する

`MONGO_URI` を Secrets Manager / SSM Parameter Store から参照する場合、App Runner サービスの Instance role に読み取り権限が必要です。`aws/apprunner-instance-role-policy.example.json` の account ID、region、resource 名を実環境に合わせて置き換えてから IAM role に付与してください。

### 4. create-service 入力 JSON を作る

`aws/apprunner-source-service.example.json` をコピーし、以下を置き換えます。

- `ServiceName`
- `ConnectionArn`
- `RepositoryUrl`
- branch 名
- `InstanceRoleArn`
- CPU / Memory

このテンプレートは `CodeConfiguration.ConfigurationSource` を `REPOSITORY` にしているため、ビルド・起動・ポート・実行時環境変数のベース設定は `apprunner.yaml` から読み込まれます。

### 5. サービスを作成する

```bash
aws apprunner create-service \
  --region ap-northeast-1 \
  --cli-input-json file://aws/apprunner-source-service.example.json
```

作成後の状態確認:

```bash
aws apprunner list-services --region ap-northeast-1
aws apprunner describe-service \
  --region ap-northeast-1 \
  --service-arn arn:aws:apprunner:ap-northeast-1:123456789012:service/learn-flask-mongodb-app/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 6. 環境変数を追加・更新する

`apprunner.yaml` には非機密の `MONGO_DB_NAME` と `LOG_LEVEL` のみを入れ、`MONGO_URI` は App Runner の環境変数として Secrets Manager / SSM Parameter Store 参照で設定する運用を推奨します。

App Runner API / CLI で更新する場合は、現在の service 設定を取得して `RuntimeEnvironmentSecrets` または `RuntimeEnvironmentVariables` を含む update 用 JSON を作成し、`update-service` を実行します。既存設定の上書き漏れを避けるため、まず `describe-service` の結果を控えてから更新してください。

```bash
aws apprunner describe-service \
  --region ap-northeast-1 \
  --service-arn YOUR_SERVICE_ARN > /tmp/apprunner-service.json

aws apprunner update-service \
  --region ap-northeast-1 \
  --cli-input-json file://YOUR_UPDATE_SERVICE_INPUT.json
```

## ECR イメージ方式で試す場合

このリポジトリには `Dockerfile` もあるため、ECR に push したイメージから App Runner サービスを作ることもできます。イメージ方式では `apprunner.yaml` は使われないため、App Runner の Image configuration で port `8080`、必要な環境変数、Instance role を設定してください。

```bash
AWS_ACCOUNT_ID=123456789012
AWS_REGION=ap-northeast-1
ECR_REPOSITORY=learn-flask-mongodb-app
IMAGE_TAG=latest

aws ecr create-repository \
  --region "$AWS_REGION" \
  --repository-name "$ECR_REPOSITORY"

aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t "$ECR_REPOSITORY:$IMAGE_TAG" .
docker tag "$ECR_REPOSITORY:$IMAGE_TAG" \
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG"
```

## トラブルシューティング

- `/health` が 500 の場合は、App Runner から MongoDB に接続できていません。`MONGO_URI`、MongoDB 側の network allowlist、VPC Connector、TLS 設定を確認してください。
- MongoDB Atlas を使う場合、App Runner からの outbound IP は固定ではありません。検証では一時的に広い allowlist を使うことがありますが、本番では VPC Peering / PrivateLink などを検討してください。
- `MONGO_URI` を Plain text で設定するとコンソールやログで見える可能性があるため、Secrets Manager または SSM Parameter Store を使ってください。
- ソースコード方式で `ConfigurationSource=REPOSITORY` の場合、ビルド・起動設定の変更は `apprunner.yaml` を commit / push して反映します。
