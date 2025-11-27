# Concurrent Streaming with Microsoft Agent Framework

ワークフローで並列実行中のエージェントの出力をストリーミング表示する Python サンプルです。

## 🚀 特徴

- **Flask**を使用したWebアプリケーション
- **Vanilla JavaScript**による完全なクライアントサイド実装
- **HTTP Chunked Transfer**によるストリーミング
- **Fetch API**でのストリーミング受信
- 通常チャットとマルチエージェント分析の両方をサポート
- リアルタイムでAI応答を表示

## 📋 必要要件

- Python 3.10以上

## 🔧 セットアップ

### 1. バックエンド (FastAPI) の起動

まず、バックエンドAPIを起動します。

#### 依存関係のインストール

```powershell
cd Backend
pip install -r requirements.txt
```

#### 環境変数の設定

Azure OpenAIの接続情報を設定します:
`.env.example` の名前を `.env` に変更して以下を記載します。

```
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

#### バックエンドの起動

```powershell
python app.py
```

デフォルトでは `http://localhost:8000` で起動します。

### 2. フロントエンド (Flask) の起動

新しいターミナルを開いて、フロントエンドを起動します。

#### 依存関係のインストール

```powershell
cd Frontend
pip install -r requirements.txt
```

#### アプリケーションの起動

```powershell
python app.py
```

デフォルトでは `http://localhost:5000` で起動します。

## 🎯 使い方

### 基本操作

1. アプリケーションが起動したら、ブラウザで `http://localhost:5000` を開く
2. メッセージ入力欄にプロンプトを入力
3. **📤 送信**ボタンで通常チャット
4. **🔀 マルチ**ボタンでマルチエージェント分析

### 環境変数

- **BACKEND_URL**: FastAPIバックエンドのURL（デフォルト: `http://localhost:8000`）

```powershell
$env:BACKEND_URL="http://localhost:8000"
python app.py
```

## 🏗️ アーキテクチャ

### ファイル構成

```
Backend/
├── app.py                    # FastAPIバックエンド
├── requirements.txt          # Python依存関係
└── .env.example              # 環境変数 (Azure OpenAI設定)

Frontend/
├── app.py                    # Flaskアプリケーション
├── requirements.txt          # Python依存関係
├── templates/
│   └── index.html           # メインHTMLテンプレート
├── static/
│   ├── css/
│   │   └── site.css        # スタイルシート
│   └── js/
│       └── app.js          # クライアントサイドJavaScript
└── README.md
```


### データフロー

```
┌─────────────────────┐
│ Browser             │
│ (Fetch API)         │
└──────────┬──────────┘
           │
           │ HTTP POST (streaming)
           ↓
┌─────────────────────┐
│ Flask Server        │
│ (/api/chat/stream)  │
└──────────┬──────────┘
           │
           │ HTTP POST (streaming)
           ↓
┌─────────────────────┐
│ FastAPI Backend     │
│ (/api/stream)       │
└──────────┬──────────┘
           │
           │ Microsoft Agent Framework
           ↓
┌─────────────────────┐
│ Azure OpenAI        │
└─────────────────────┘
```

## 📝 ライセンス

MIT License
