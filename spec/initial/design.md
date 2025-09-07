# 1.0 システムアーキテクチャ
## 1.1 ハイレベルアーキテクチャ図
システムは、Next.jsによるフロントエンド、Python/FastAPIによるバックエンド、データベース、そして外部のGemini APIから構成される、マイクロサービス指向のアーキテクチャを採用します。
```
graph TD
    subgraph User Device
        A
    end

    subgraph GCP
        subgraph Cloud Run Service 1
            B
        end
        subgraph Cloud Run Service 2
            C
        end
        subgraph Cloud SQL
            D
        end
    end

    subgraph Google AI
        E[Gemini API]
    end

    A -- HTTPS --> B
    B -- gRPC/HTTP --> C
    C -- SQL --> D
    C -- HTTPS --> E
```

## 1.2 技術スタックの正当性
- Next.js (フロントエンド): モダンなReactアプリケーション構築のための強力なフレームワーク。高速な初期表示を実現するSSRや、セキュアなBFF(Backend for Frontend)を構築するためのAPI Routes機能が採用理由。
- Python/FastAPI (バックエンド): 高パフォーマンス、シンプルな開発体験、そしてAI/データ処理関連の豊富なエコシステムが特徴。AIコパイロット機能の実装に最適。
- Gemini API: 高度な推論能力とFunction Calling機能を持ち、本サービスのAIコパイロットの中核を担う。
- GCP (Cloud Run & Cloud SQL): サーバーレスでスケーラブルなインフラを提供。運用オーバーヘッドを最小限に抑え、スタートアップのコスト効率を最大化する

## 1.3 GCPインフラ: Cloud Runパラダイムの採用
本サービスのインフラには、GKE（Google Kubernetes Engine）ではなくCloud Runを選択します。Cloud Runは、ステートレスなコンテナ化されたアプリケーションに最適なフルマネージドのサーバーレスプラットフォームです 3。トラフィックに応じて自動的にスケールし、リクエストがない場合はゼロにスケールダウンするため、特にトラフィックが予測不能なサービス初期段階において高いコスト効率を実現します 5。この選択は、将来的なBtoB展開への柔軟性も確保します。BtoBのエンタープライズ顧客は、より厳格なネットワーク（VPC）やセキュリティ要件、リソースの細かな制御を求める傾向があり、これらはGKEの方が適している場合があります 6。しかし、Cloud RunとGKEは共に標準的なコンテナイメージをデプロイメントの単位とするため、両者間の移植性は非常に高いです 7。したがって、初期段階ではCloud Runのシンプルさとコスト効率の恩恵を受けつつ、将来のBtoB展開の際には、アプリケーションコードを変更することなく、デプロイ環境をGKEへ移行することが可能です。この戦略的柔軟性を確保するため、アプリケーションは12-Factor Appの原則に準拠し、すべての設定は環境変数を通じて管理される設計とします。

# 2.0 データアーキテクチャ
## 2.1 論理データモデル (ERD)
```
erDiagram
    users {
        UUID id PK
        VARCHAR email UK
        VARCHAR password_hash
        VARCHAR subscription_tier
        TIMESTAMPZ created_at
    }

    business_frameworks {
        UUID id PK
        VARCHAR name
        TEXT description
        JSONB micro_content
    }

    user_outputs {
        UUID id PK
        UUID user_id FK
        UUID framework_id FK
        JSONB output_data
        TIMESTAMPZ created_at
    }

    company_profiles {
        UUID id PK
        UUID user_id FK
        VARCHAR profile_name
        JSONB profile_data
    }

    user_progress {
        UUID id PK
        UUID user_id FK
        VARCHAR event_type
        UUID entity_id
        INTEGER points_awarded
        JSONB metadata
        TIMESTAMPTZ created_at
    }

    user_learning_sessions {
        UUID id PK
        UUID user_id FK
        UUID framework_id FK
        TIMESTAMPTZ started_at
        TIMESTAMPTZ completed_at
        JSONB learning_data
        VARCHAR status
    }

    notification_preferences {
        UUID id PK
        UUID user_id FK
        BOOLEAN email_enabled
        BOOLEAN push_enabled
        JSONB reminder_settings
        TIMESTAMPTZ updated_at
    }

    notification_history {
        UUID id PK
        UUID user_id FK
        VARCHAR notification_type
        VARCHAR delivery_channel
        JSONB content
        TIMESTAMPTZ scheduled_at
        TIMESTAMPTZ sent_at
        VARCHAR status
    }

    output_versions {
        UUID id PK
        UUID output_id FK
        INTEGER version_number
        JSONB version_data
        TIMESTAMPTZ created_at
        BOOLEAN is_current
    }

    user_badges {
        UUID id PK
        UUID user_id FK
        VARCHAR badge_type
        VARCHAR badge_name
        JSONB badge_metadata
        TIMESTAMPTZ earned_at
    }

    users |--o{ user_outputs : "creates"
    users |--o{ company_profiles : "owns"
    users |--o{ user_progress : "has"
    users |--o{ user_learning_sessions : "participates_in"
    users |--o{ notification_preferences : "configures"
    users |--o{ notification_history : "receives"
    users |--o{ user_badges : "earns"
    business_frameworks |--o{ user_outputs : "is_based_on"
    business_frameworks |--o{ user_learning_sessions : "used_in"
    user_outputs |--o{ output_versions : "has_versions"
```

## 2.2 データベーススキーマ定義 (SQL DDL)
本サービスの永続化層としてCloud SQL for PostgreSQLを使用します。以下は主要なテーブルのDDLです。


|Table Name|Column Name|Data Type|Constraints|Description|
|:----|:----|:----|:----|:----|
|users|id|UUID|PRIMARY KEY|ユーザーの一意な識別子|
| |email|VARCHAR(255)|UNIQUE, NOT NULL|ログインに使用するメールアドレス|
| |password_hash|VARCHAR(255)|NOT NULL|ハッシュ化されたパスワード|
| |subscription_tier|VARCHAR(50)|DEFAULT 'free'|free' または 'premium'|
| |created_at|TIMESTAMPTZ|NOT NULL|ユーザー作成日時|
|business_frameworks|id|UUID|PRIMARY KEY|フレームワークの一意な識別子|
| |name|VARCHAR(100)|NOT NULL|例: 'SWOT Analysis'|
| |description|TEXT| |フレームワークの詳細な説明|
| |micro_content|JSONB| |学習コンテンツ（テキスト、画像URLなど）|
|user_outputs|id|UUID|PRIMARY KEY|アウトプットの一意な識別子|
| |user_id|UUID|FK to users.id|作成したユーザー|
| |framework_id|UUID|FK to frameworks.id|使用したフレームワーク|
| |output_data|JSONB|NOT NULL|構造化されたアウトプットデータ|
| |created_at|TIMESTAMPTZ|NOT NULL|作成日時|
|user_progress|id|UUID|PRIMARY KEY|進捗イベントの一意識別子|
| |user_id|UUID|FK to users.id|進捗を記録するユーザー|
| |event_type|VARCHAR(50)|NOT NULL|例: 'LESSON_COMPLETED', 'BADGE_EARNED'|
| |entity_id|UUID| |関連エンティティID（フレームワーク等）|
| |points_awarded|INTEGER| |獲得ポイント|
| |metadata|JSONB| |追加情報（例: AIによる品質スコア）|
| |created_at|TIMESTAMPTZ|NOT NULL|イベント発生日時|
|user_learning_sessions|id|UUID|PRIMARY KEY|学習セッションの一意識別子|
| |user_id|UUID|FK to users.id|学習者|
| |framework_id|UUID|FK to business_frameworks.id|学習したフレームワーク|
| |started_at|TIMESTAMPTZ|NOT NULL|セッション開始時刻|
| |completed_at|TIMESTAMPTZ| |セッション完了時刻|
| |learning_data|JSONB| |学習内容と進捗データ|
| |status|VARCHAR(20)|NOT NULL|'in_progress', 'completed', 'abandoned'|
|notification_preferences|id|UUID|PRIMARY KEY|通知設定の一意識別子|
| |user_id|UUID|FK to users.id, UNIQUE|設定対象ユーザー|
| |email_enabled|BOOLEAN|DEFAULT true|メール通知の有効/無効|
| |push_enabled|BOOLEAN|DEFAULT true|プッシュ通知の有効/無効|
| |reminder_settings|JSONB| |リマインダー設定（時間、頻度等）|
| |updated_at|TIMESTAMPTZ|NOT NULL|設定更新日時|
|notification_history|id|UUID|PRIMARY KEY|通知履歴の一意識別子|
| |user_id|UUID|FK to users.id|通知対象ユーザー|
| |notification_type|VARCHAR(50)|NOT NULL|'reminder', 'achievement', 'review'|
| |delivery_channel|VARCHAR(20)|NOT NULL|'email', 'push', 'in_app'|
| |content|JSONB|NOT NULL|通知内容|
| |scheduled_at|TIMESTAMPTZ|NOT NULL|配信予定時刻|
| |sent_at|TIMESTAMPTZ| |実際の配信時刻|
| |status|VARCHAR(20)|NOT NULL|'pending', 'sent', 'failed'|
|output_versions|id|UUID|PRIMARY KEY|バージョンの一意識別子|
| |output_id|UUID|FK to user_outputs.id|元のアウトプット|
| |version_number|INTEGER|NOT NULL|バージョン番号（1から開始）|
| |version_data|JSONB|NOT NULL|このバージョンのデータ|
| |created_at|TIMESTAMPTZ|NOT NULL|バージョン作成日時|
| |is_current|BOOLEAN|DEFAULT false|現在のバージョンかどうか|
|user_badges|id|UUID|PRIMARY KEY|バッジの一意識別子|
| |user_id|UUID|FK to users.id|バッジ獲得者|
| |badge_type|VARCHAR(50)|NOT NULL|'beginner', 'explorer', 'expert', 'consistent', 'master'|
| |badge_name|VARCHAR(100)|NOT NULL|バッジ名|
| |badge_metadata|JSONB| |バッジ獲得条件や詳細|
| |earned_at|TIMESTAMPTZ|NOT NULL|バッジ獲得日時|


# 3.0 バックエンド設計 (Python/FastAPI)
## 3.1 API設計思想
APIはRESTfulの原則に準拠します。標準的なHTTPメソッド（GET, POST, PUT, DELETE）、ステータスコード、リクエスト/レスポンスボディにはJSON形式を使用します。
## 3.2 APIエンドポイント仕様
以下は、フロントエンドとバックエンド間の契約となる主要なAPIエンドポイントの仕様です。

|Endpoint|Method|Description|Auth Required|Request Body|Success Response|
|:----|:----|:----|:----|:----|:----|
|/auth/register|POST|新規ユーザー登録|No|{email, password}|201 Created|
|/auth/login|POST|ユーザーログイン|No|{email, password}|200 OK (sets cookie)|
|/auth/logout|POST|ユーザーログアウト|Yes|(empty)|200 OK (clears cookie)|
|/users/me|GET|ログイン中ユーザーのプロファイル取得|Yes|(empty)|200 OK {id, email, tier}|
|/users/preferences|GET|ユーザー設定の取得|Yes|(empty)|200 OK {...preferences}|
|/users/preferences|PUT|ユーザー設定の更新|Yes|{notification_settings}|200 OK|
|/users/data-export|POST|ユーザーデータエクスポート|Yes|(empty)|200 OK {download_url}|
|/users/delete|DELETE|アカウント削除|Yes|(empty)|202 Accepted|
|/frameworks|GET|全フレームワークのリスト取得|Yes (Free)|(empty)|200 OK [...frameworks]|
|/frameworks/{id}|GET|特定フレームワークの詳細取得|Yes (Free)|(empty)|200 OK {...framework_details}|
|/ai/interact|POST|AIコパイロットとの対話|Yes (Premium)|{framework_id, history, input}|200 OK {ai_response}|
|/outputs|POST|新規アウトプットの保存|Yes (Premium)|{framework_id, output_data}|201 Created|
|/outputs|GET|ユーザーのアウトプット一覧取得|Yes (Premium)|(empty)|200 OK [...outputs]|
|/outputs/{id}|GET|特定アウトプットの取得|Yes (Premium)|(empty)|200 OK {...output_details}|
|/outputs/{id}|PUT|アウトプットの更新|Yes (Premium)|{output_data}|200 OK|
|/outputs/{id}/versions|GET|アウトプットのバージョン履歴取得|Yes (Premium)|(empty)|200 OK [...versions]|
|/outputs/{id}/versions/{version}|POST|特定バージョンへの復元|Yes (Premium)|(empty)|200 OK|
|/notifications|GET|通知一覧の取得|Yes|(empty)|200 OK [...notifications]|
|/notifications/{id}/read|POST|通知を既読にする|Yes|(empty)|200 OK|
|/learning/sessions|POST|学習セッション開始|Yes (Premium)|{framework_id}|201 Created {session_id}|
|/learning/sessions/{id}|PUT|学習セッション更新|Yes (Premium)|{learning_data, status}|200 OK|
|/learning/schedule|GET|復習スケジュール取得|Yes|(empty)|200 OK [...schedule]|
|/progress/badges|GET|獲得バッジ一覧取得|Yes|(empty)|200 OK [...badges]|
|/progress/points|GET|ポイント履歴取得|Yes|(empty)|200 OK {...points_summary}|

## 3.3 認証・認可フロー
認証にはステートレスなJWT（JSON Web Token）ベースの方式を採用します。セキュリティのベストプラクティスに従い、JWTはlocalStorageではなく、XSS（クロスサイトスクリプティング）攻撃に対して安全なHttpOnly属性を持つCookieに保存します。
このHttpOnly Cookieの採用は、システムアーキテクチャに重要な影響を与えます。ブラウザ上で動作するJavaScript（Next.jsのクライアントコンポーネント）はHttpOnly Cookieに直接アクセスできないため、Pythonバックエンドへの認証付きリクエストを直接送信できません。この問題を解決するため、Next.jsのサーバーサイド機能を利用したBFF（Backend for Frontend）パターンを導入します。

認証フローシーケンス:
1. クライアントコンポーネントは、Next.jsのAPI Route（例: /api/proxy/users/me）にリクエストを送信します。
2. サーバーサイドで実行される**Next.js API Route (BFF)**は、ブラウザから自動的に送信されるHttpOnly Cookieを受け取ります。
3. BFFはCookieからJWTを抽出し、Pythonバックエンド（例: http://python-service/users/me）への新しいリクエストを作成します。その際、Authorization: Bearer <token>ヘッダーを付与します。
4. PythonバックエンドはJWTを検証し、リクエストを処理してデータを返却します。
5. BFFはPythonバックエンドからのレスポンスを、そのままクライアントコンポーネントに返します。このアーキテクチャにより、フロントエンドのモダンな開発体験と、堅牢なセキュリティを両立させます。

# 4.0 AIコア設計: Geminiコパイロット
## 4.1 対話シーケンス図
```
sequenceDiagram
    participant User
    participant Frontend (Next.js)
    participant BFF (Next.js API Route)
    participant Backend (Python/FastAPI)
    participant Gemini_API

    User->>Frontend: 思考を入力
    Frontend->>BFF: POST /api/proxy/ai/interact
    BFF->>Backend: POST /ai/interact (with JWT)
    Backend->>Gemini_API: generateContent(prompt, tools)
    Gemini_API-->>Backend: functionCall(analyze_swot, args)
    Backend->>Backend: 内部ロジック実行 (e.g., ユーザー入力の整理)
    Backend->>Gemini_API: generateContent(prompt, functionResponse)
    Gemini_API-->>Backend: textResponse("次の質問です...")
    Backend-->>BFF: AIからの応答
    BFF-->>Frontend: AIからの応答
    Frontend-->>User: 応答を表示
```

## 4.2 Gemini Function Calling 仕様
AIコパイロットの能力は、GeminiのFunction Calling機能をいかに効果的に利用するかにかかっています。この機能は、単に外部APIを呼び出すだけでなく、LLMとの対話を構造化し、特定の目的に沿ってガイドするための強力なメカニズムです。
サービスの目的は自由なチャットではなく、特定のビジネスフレームワークに沿った分析を支援することです。そのため、各フレームワークに対応するFunction Declaration（関数宣言）を精密に設計します。この宣言は、AIに対して「どのような情報を」「どのような形式で」ユーザーから引き出すべきかを指示するスキーマとして機能します。AIの役割は、このスキーマを埋めるために、ユーザーに対話形式で質問を投げかけることになります。これにより、AIとの対話は目的志向で一貫性のあるものとなり、高品質なアウトプット生成へと繋がります。

|Framework|Function Name|Description|Parameters|
|:----|:----|:----|:----|
|SWOT Analysis|analyze_swot|企業の内部環境である「強み」「弱み」と、外部環境である「機会」「脅威」を特定し、企業の現状を分析する。4つの象限それぞれについて情報を収集する。|{ "type": "object", "properties": { "strengths": { "type": "array", "items": { "type": "string" }, "description": "自社が持つ、競合に対する優位性や特長。" }, "weaknesses": { "type": "array", "items": { "type": "string" }, "description": "自社が持つ、競合に対する不利な点や課題。" }, "opportunities": { "type": "array", "items": { "type": "string" }, "description": "市場成長や規制緩和など、自社にとって追い風となる外部要因。" }, "threats": { "type": "array", "items": { "type": "string" }, "description": "競合の台頭や技術革新など、自社にとって逆風となる外部要因。" } }, "required": ["strengths", "weaknesses", "opportunities", "threats"] }|
|User Journey Map|create_user_journey|特定のペルソナが製品やサービスを認知し、利用し、最終的なゴールに至るまでの一連の体験を時系列で可視化する。各ステージでの行動、思考、感情、課題点を明らかにする。|{ "type": "object", "properties": { "persona": { "type": "string", "description": "このジャーニーを体験するユーザーペルソナの名前や特徴。" }, "stages": { "type": "array", "items": { "type": "object", "properties": { "stage_name": { "type": "string", "description": "ジャーニーの段階名（例: 認知、検討、購入）。" }, "user_actions": { "type": "string", "description": "この段階でユーザーが具体的に行う行動。" }, "pain_points": { "type": "string", "description": "この段階でユーザーが感じる不満や課題。" } } } } }, "required": ["persona", "stages"] }|

## 4.3 通知システム設計
### 4.3.1 通知アーキテクチャ
通知システムは、エビングハウス忘却曲線に基づいた復習タイミングの計算と、多チャネル配信を管理する。

#### コンポーネント構成:
- **Notification Scheduler**: Cloud Schedulerを使用した定期実行
- **Review Calculator**: 学習履歴から復習タイミングを計算
- **Notification Queue**: Redis Queueを使用した非同期処理
- **Delivery Manager**: プッシュ通知、メール、アプリ内通知の配信制御

### 4.3.2 エビングハウス復習スケジューリング
学習完了時に以下の復習スケジュールを自動生成:

```python
def calculate_review_schedule(learning_completion_time):
    intervals = [1, 3, 7, 30]  # days
    schedule = []
    for interval in intervals:
        review_time = learning_completion_time + timedelta(days=interval)
        schedule.append({
            'scheduled_at': review_time,
            'interval_days': interval,
            'retention_rate': get_retention_rate(interval)
        })
    return schedule
```

### 4.3.3 通知配信ロジック
- **優先度**: 復習通知 > 達成通知 > リマインダー
- **頻度制限**: 1日最大3通知まで
- **時間帯制御**: ユーザー設定に基づく配信時間
- **チャネル選択**: 通知タイプと緊急度に応じた最適チャネル選択

# 5.0 フロントエンド設計 (Next.js)
## 5.1 コンポーネントアーキテクチャ
アプリケーションは再利用可能なコンポーネント群で構築されます。主要なコンポーネントは以下の通りです。

### 基本コンポーネント
- **Layout**: 全ページ共通のヘッダー、フッター、ナビゲーションを含む
- **Dashboard**: ログイン後のホームページ。学習進捗やおすすめコンテンツを表示
- **FrameworkLibrary**: ビジネスフレームワークの一覧を表示するコンポーネント
- **FrameworkViewer**: 個別のフレームワークのマイクロコンテンツを表示するコンポーネント
- **AiInteractionPanel**: AIコパイロットとの対話を行うチャットUI
- **SwotOutputDisplay**: SWOT分析の結果を2x2のマトリクスで表示するコンポーネント

### 新規追加コンポーネント
- **NotificationCenter**: アプリ内通知の表示・管理を行うドロップダウンコンポーネント
- **LearningSchedule**: エビングハウス曲線に基づく復習スケジュールを表示
- **BadgeDisplay**: 獲得したバッジを表示するコンポーネント（グリッド表示とバッジ詳細モーダル）
- **VersionHistory**: アウトプットのバージョン履歴を表示・管理するサイドパネル
- **UserPreferences**: 通知設定やその他のユーザー設定を管理するフォーム
- **ProgressTracker**: ポイント、連続ログイン日数、学習統計を可視化
- **ReviewQuiz**: 復習時に表示するクイズコンポーネント
- **NotificationToast**: プッシュ通知のトースト表示

## 5.2 状態管理戦略
- コンポーネントローカルな状態管理には、React標準のuseState, useContextフックを利用します。
- サーバーからのデータ取得やキャッシュ、再検証といったサーバー状態の管理には、SWRやReact Queryのような専用ライブラリを導入し、効率的なデータフェッチングを実現します。

## 5.3 APIクライアントとデータフェッチング
Next.js BFFプロキシエンドポイントとの通信を抽象化するため、専用のAPIクライアントモジュールを作成します。これにより、データフェッチングロジックを一元管理し、コードの保守性を高めます。

# 6.0 DevOpsと環境
## 6.1 GCPプロジェクト設定
サービスのデプロイには、GCPプロジェクトの適切な設定が不可欠です。
- 新規GCPプロジェクトを作成し、課金を有効化する。
- Cloud Run, Cloud Build, Artifact Registry, Cloud SQL APIを有効化する。
- Cloud RunサービスがCloud SQLに接続するためのIAMロール（roles/cloudsql.client）や、サービス間呼び出しのためのロール（roles/run.invoker）を持つサービスアカウントを作成する。

## 6.2 環境変数管理
開発環境と本番環境の切り替えを容易にするため、設定は.envファイルを通じて管理します。
リポジトリには.env.templateファイルをコミットし、実際の値は各環境で設定します。

|Variable Name|Service|Description|Example Value (Dev)|
|:----|:----|:----|:----|
|DATABASE_URL|Backend|PostgreSQLへの接続文字列|postgresql://user:pass@localhost:5432/bizdesign|
|JWT_SECRET_KEY|Backend|JWT署名用の秘密鍵|a-very-secret-key|
|GEMINI_API_KEY|Backend|Google GeminiのAPIキー|AIzaSy...|
|REDIS_URL|Backend|Redisへの接続文字列|redis://localhost:6379/0|
|NOTIFICATION_QUEUE_URL|Backend|通知キュー用Redis URL|redis://localhost:6379/1|
|SENDGRID_API_KEY|Backend|メール送信用SendGrid APIキー|SG.xxxxx|
|PUSH_NOTIFICATION_KEY|Backend|プッシュ通知用のサービスキー|xxxxx|
|CLOUD_SCHEDULER_PROJECT_ID|Backend|Cloud SchedulerのプロジェクトID|biz-design-prod|
|DATA_RETENTION_DAYS|Backend|データ保持期間（日数）|2555|
|NEXT_PUBLIC_API_URL|Frontend|Next.js BFFのベースURL|http://localhost:3000/api/proxy|
|BACKEND_API_URL|Frontend (BFF)|Pythonバックエンドの内部URL|http://localhost:8000|
|NEXT_PUBLIC_PUSH_VAPID_KEY|Frontend|プッシュ通知用VAPID公開鍵|BxxxxxxxxxxxxQ|

## 6.3 Cloud BuildによるCI/CDパイプライン
Cloud Buildを利用して、GitリポジトリへのプッシュをトリガーとしたCI/CDパイプラインを構築します。
cloudbuild.yamlファイルに以下のステップを定義します。

1. mainブランチへのプッシュをトリガーにビルドを開始する。
2. Next.jsとFastAPIサービスのDockerイメージをそれぞれビルドする。
3. ビルドしたイメージをGoogle Artifact Registryにプッシュする。
4. 新しいイメージをそれぞれのCloud Runサービスにデプロイする。

# 7.0 セキュリティとプライバシー設計
## 7.1 データプライバシー実装設計
### GDPR準拠のデータ削除フロー
ユーザーがアカウント削除を要求した場合の処理フロー:

```python
async def delete_user_account(user_id: str):
    # 1. ソフトデリート（即座に実行）
    await mark_user_deleted(user_id)
    
    # 2. 関連データの匿名化（24時間以内）
    await anonymize_user_outputs(user_id)
    await anonymize_progress_data(user_id)
    
    # 3. 物理削除をスケジュール（30日後）
    await schedule_physical_deletion(user_id, days=30)
    
    # 4. バックアップからの削除をスケジュール（180日後）
    await schedule_backup_deletion(user_id, days=180)
```

### データエクスポート機能
- **対象データ**: プロファイル、学習履歴、作成したアウトプット、進捗データ
- **形式**: JSON（構造化）+ CSV（分析用）
- **生成時間**: 大規模データでも15分以内
- **ダウンロード期限**: 生成後7日間有効

## 7.2 APIレート制限の実装
### レート制限アルゴリズム
Sliding Window Log方式を採用し、正確なレート制限を実現:

```python
class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(self, user_id: str, endpoint: str) -> bool:
        key = f"rate_limit:{user_id}:{endpoint}"
        now = time.time()
        window = 3600  # 1時間
        
        # 古い記録を削除
        await self.redis.zremrangebyscore(key, 0, now - window)
        
        # 現在のリクエスト数を確認
        current_count = await self.redis.zcard(key)
        limit = self.get_limit(endpoint, user_tier)
        
        if current_count >= limit:
            return False
            
        # リクエストを記録
        await self.redis.zadd(key, {str(uuid.uuid4()): now})
        await self.redis.expire(key, window)
        return True
```

## 7.3 セキュリティ監視とログ
### 監査ログの設計
- **記録対象**: 認証、データアクセス、設定変更、削除操作
- **保存期間**: 180日間（法的要件に準拠）
- **ログ形式**: 構造化JSON + 暗号化
- **異常検知**: 不正アクセスパターンの自動検知とアラート
