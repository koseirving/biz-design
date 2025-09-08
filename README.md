# Biz Design - AI活用型ビジネスフレームワーク学習プラットフォーム

## 概要

Biz Designは、AI活用型学習とビジネスフレームワーク教育を組み合わせた総合プラットフォームです。SWOT分析、カスタマージャーニーマッピング、その他のビジネス手法をGemini AIで強化し、インタラクティブな学習体験を提供します。

## アーキテクチャ

- **フロントエンド**: Next.js 15（TypeScript、TailwindCSS）
- **バックエンド**: FastAPI（Python 3.11）
- **データベース**: PostgreSQL（SQLAlchemy）
- **キャッシュ/キュー**: Redis
- **AI**: Google Gemini API
- **インフラ**: Google Cloud Platform（Cloud Run、Cloud SQL、Memorystore）

## プロジェクト構成

```
biz-design-repo/
├── frontend/          # Next.jsアプリケーション
├── backend/           # FastAPIアプリケーション
├── spec/              # プロジェクト仕様書
└── README.md
```

## 実装済み機能

### ✅ モジュール1: プロジェクトセットアップと基盤構築
- GCPプロジェクトの初期化
- Gitリポジトリのセットアップ
- Hello Worldアプリケーション
- 基本的なCI/CDパイプライン

### ✅ モジュール2: データベースとユーザー認証
- PostgreSQLデータベースのセットアップ
- JWT認証によるユーザー登録/ログイン
- Redisキャッシング
- データプライバシー機能（GDPR準拠）

### ✅ モジュール3: コアコンテンツとバージョン管理
- ビジネスフレームワークコンテンツ管理
- アウトプットのバージョン管理
- 自動保存機能
- 学習セッション追跡

### ✅ モジュール4: AIコパイロット（Gemini連携）
- Gemini API統合
- 分析用ファンクション呼び出し
- インタラクティブAIチャットインターフェース
- アウトプット可視化

### ✅ モジュール5: プレミアム機能とゲーミフィケーション
- 企業プロファイル管理
- ポイントとバッジシステム
- 進捗追跡
- AI評価機能

### ✅ モジュール7: 通知システムとエビングハウス復習機能
- Redisベースの通知キュー
- SendGridによるメール通知
- 間隔反復学習システム
- WebSocketリアルタイム通知

### ✅ モジュール8: フロントエンド新規コンポーネント
- バージョン履歴管理
- バッジコレクション表示
- 通知センター
- エクスポート機能

### ✅ モジュール9: セキュリティとプライバシー
- **GDPR準拠**: 完全な同意管理、データ最小化
- **データエクスポート**: マルチフォーマット対応（JSON/CSV/XML/PDF/ZIP）
- **アカウント削除**: 段階的削除プロセス（ソフト削除 → 匿名化 → 完全削除）
- **レート制限**: 高度なマルチ戦略レート制限
- **暗号化**: AES-256-GCM、Fernet、RSA-OAEP、ハイブリッド暗号化
- **監査ログ**: 包括的なセキュリティイベント追跡
- **アクセシビリティ**: WCAG 2.1レベルAA準拠

## セキュリティ機能

### データ保護
- **保存時の暗号化**: 機密データのAES-256-GCM暗号化
- **通信時の暗号化**: すべての通信にTLS 1.3を使用
- **フィールドレベル暗号化**: 機密フィールドの選択的暗号化
- **キー管理**: GCP Secret Managerとの統合

### アクセス制御
- **レート制限**: スライディングウィンドウ、固定ウィンドウ、トークンバケット戦略
- **サブスクリプション別制限**: 無料/プレミアムユーザーで異なる制限
- **APIセキュリティ**: 包括的な入力検証とサニタイゼーション

### 監査とコンプライアンス
- **セキュリティ監査ログ**: 180日間保持、整合性検証付き
- **GDPRコンプライアンス**: データ主体の権利を完全実装
- **インシデント報告**: 自動セキュリティインシデント追跡
- **リアルタイム監視**: プロアクティブなセキュリティアラート

### アクセシビリティ
- **WCAG 2.1 AA**: ウェブアクセシビリティ標準に完全準拠
- **キーボードナビゲーション**: 完全なキーボードアクセシビリティ
- **スクリーンリーダーサポート**: 包括的な支援技術サポート
- **フォーカス管理**: 適切なフォーカストラップとインジケーター

## はじめに

### 前提条件
- Node.js 18以上
- Python 3.11以上
- PostgreSQL 14以上
- Redis 6以上
- Google Cloud SDK（デプロイ用）

### 開発環境のセットアップ

#### バックエンドセットアップ
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envを編集して設定を行う

# データベースマイグレーションの実行
alembic upgrade head

# サーバーの起動
uvicorn main:app --reload
```

#### フロントエンドセットアップ
```bash
cd frontend
npm install

# 環境変数の設定
cp .env.example .env.local
# .env.localを編集して設定を行う

# 開発サーバーの起動
npm run dev
```

### テスト

#### バックエンドテスト
```bash
cd backend
pytest tests/ -v
```

#### フロントエンドテスト
```bash
cd frontend
# ユニットテスト
npm test

# E2Eテスト
npm run test:e2e
```

### 環境変数

#### バックエンド (.env)
```
DATABASE_URL=postgresql://user:pass@localhost/bizdesign
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_key
JWT_SECRET_KEY=your_jwt_secret
ENCRYPTION_MASTER_KEY=your_encryption_key
SENDGRID_API_KEY=your_sendgrid_key
```

#### フロントエンド (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## APIドキュメント

バックエンドサーバー実行時に以下を参照:
- **OpenAPI ドキュメント**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要なAPIエンドポイント

#### 認証
- `POST /auth/register` - ユーザー登録
- `POST /auth/login` - ユーザーログイン
- `POST /auth/refresh` - トークン更新

#### AIコパイロット
- `POST /ai/interact` - 分析用AIインタラクション
- `GET /frameworks` - 利用可能なビジネスフレームワーク

#### セキュリティ＆プライバシー
- `POST /gdpr/consent/record` - GDPR同意の記録
- `POST /users/data-export` - ユーザーデータのエクスポート
- `POST /users/request-deletion` - アカウント削除のリクエスト
- `GET /audit/logs` - セキュリティ監査ログの照会

## デプロイメント

### Google Cloud Platform

#### バックエンド (Cloud Run)
```bash
# ビルドとデプロイ
gcloud run deploy biz-design-backend \
  --source . \
  --platform managed \
  --region us-central1
```

#### フロントエンド (Cloud Run)
```bash
# ビルドとデプロイ
gcloud run deploy biz-design-frontend \
  --source . \
  --platform managed \
  --region us-central1
```

### データベースマイグレーション
```bash
# 本番環境でのマイグレーション実行
alembic upgrade head
```

## 監視と可観測性

- **ログ**: Google Cloud Loggingによる構造化JSONログ
- **メトリクス**: ビジネスおよびセキュリティイベント用カスタムメトリクス
- **アラート**: セキュリティインシデントの自動アラート
- **ヘルスチェック**: 包括的なヘルス監視

## セキュリティ上の考慮事項

### 本番環境チェックリスト
- [ ] HTTPSのみを有効化
- [ ] 適切なCORSオリジンを設定
- [ ] レート制限を設定
- [ ] 監査ログを有効化
- [ ] 暗号化キーを設定
- [ ] 監視アラートを設定
- [ ] アクセス制御をレビュー
- [ ] バックアップ/リカバリ手順をテスト

## コントリビュート

1. リポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## サポート

質問やサポートについては、開発チームにお問い合わせいただくか、リポジトリにイシューを作成してください。

---

**ステータス**: ✅ モジュール1-9 完了 | 🚧 モジュール10（デプロイメント）進行中