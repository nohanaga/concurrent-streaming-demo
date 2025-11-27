import os
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from agent_framework import ConcurrentBuilder, AgentRunUpdateEvent, WorkflowOutputEvent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

load_dotenv()

app = FastAPI()

# CORS設定を追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",   # Flask / .NET
        "https://localhost:5001",  # .NET (HTTPS)
        "http://localhost:8501",   # Streamlit
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Agent Framework Chat Clientの初期化
chat_client = None

if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT:
    chat_client = AzureOpenAIChatClient(
        api_key=AZURE_OPENAI_API_KEY,
        endpoint=AZURE_OPENAI_ENDPOINT,
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
    )

# エージェントの作成
critical_agent = None
positive_agent = None
synthesizer_agent = None

if chat_client:
    # 批判的エージェント
    critical_agent = chat_client.create_agent(
        name="CriticalAnalyst",
        instructions="""
あなたは批判的思考の専門家です。
ユーザーの質問やアイデアに対して、潜在的な問題点、リスク、改善が必要な点を指摘します。
徹底的な批判を行い、具体的な懸念事項を簡潔に述べてください。
"""
    )
    
    # 肯定的エージェント
    positive_agent = chat_client.create_agent(
        name="PositiveAdvocate",
        instructions="""
あなたは肯定的思考の専門家です。
ユーザーの質問やアイデアに対して、利点、機会、成功の可能性を強調します。
前向きな視点から価値を見出し、具体的なメリットを簡潔に述べてください。
"""
    )
    
    # 統合エージェント
    synthesizer_agent = chat_client.create_agent(
        name="Synthesizer",
        instructions="""
あなたは統合の専門家です。
批判的な視点と肯定的な視点の両方を考慮し、バランスの取れた総合的な分析を提供します。
両方の視点を統合し、実用的な結論を導き出してください。
"""
    )


@app.post("/api/stream")
async def api_stream(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    if not prompt:
        return JSONResponse({"error": "prompt required"}, status_code=400)

    async def generator():
        if chat_client is None:
            yield "Error: Azure OpenAI configuration is missing"
            return

        # 簡易エージェントを作成
        simple_agent = chat_client.create_agent(
            instructions="あなたは親切なアシスタントです。質問に簡潔に答えてください。"
        )
        
        # ストリーミングレスポンスを取得
        async for update in simple_agent.run_stream(prompt):
            if update.text:
                yield update.text

    return StreamingResponse(generator(), media_type="text/plain")


@app.post("/api/multi-agent-stream")
async def multi_agent_stream(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    if not prompt:
        return JSONResponse({"error": "prompt required"}, status_code=400)

    async def generator():
        if not all([critical_agent, positive_agent, synthesizer_agent]):
            yield "Error: Multi-agent system is not properly configured\n"
            return

        try:
            import json
            
            yield "=== マルチエージェント分析開始 ===\n\n"
            yield json.dumps({"type": "start"}, ensure_ascii=False) + "\n"
            
            # ConcurrentBuilderを使用して並列ワークフローを作成
            agents = [critical_agent, positive_agent]
            workflow = ConcurrentBuilder().participants(agents).build()
            
            # エージェントの結果を格納
            agent_results = {}
            
            # ワークフローをストリーミング実行
            async for event in workflow.run_stream(prompt):
                # AgentRunUpdateEvent: エージェントからのストリーミング更新
                if isinstance(event, AgentRunUpdateEvent):
                    # executor_idからエージェント名を取得
                    agent_name = event.executor_id
                    
                    # AgentRunResponseUpdateからテキストを取得
                    if event.data and hasattr(event.data, 'text') and event.data.text:
                        data = {
                            "agent": agent_name,
                            "content": event.data.text,
                            "is_final": False
                        }
                        yield json.dumps(data, ensure_ascii=False) + "\n"
                
                # WorkflowOutputEvent: ワークフローからの最終出力
                elif isinstance(event, WorkflowOutputEvent):
                    # 並行エージェントの結果を収集
                    # event.dataはChatMessageのリスト
                    if event.data:
                        for msg in event.data:
                            if hasattr(msg, 'author_name') and hasattr(msg, 'text'):
                                agent_results[msg.author_name] = msg.text
            
            yield json.dumps({"type": "agents_complete"}, ensure_ascii=False) + "\n"
            
            # 統合分析をストリーム
            yield json.dumps({"type": "synthesis_start"}, ensure_ascii=False) + "\n"
            
            # 両方の結果をまとめて統合エージェントに渡す
            critical_content = agent_results.get("CriticalAnalyst", "")
            positive_content = agent_results.get("PositiveAdvocate", "")
            
            synthesis_prompt = f"""
以下の2つの視点を統合して、バランスの取れた分析を提供してください。

元の質問: {prompt}

批判的視点:
{critical_content}

肯定的視点:
{positive_content}
"""
            
            # 統合エージェントの応答をストリーミング
            async for update in synthesizer_agent.run_stream(synthesis_prompt):
                if update.text:
                    data = {
                        "agent": "Synthesizer",
                        "content": update.text,
                        "is_final": False
                    }
                    yield json.dumps(data, ensure_ascii=False) + "\n"
            
            yield json.dumps({"type": "complete"}, ensure_ascii=False) + "\n"
            
        except Exception as e:
            import traceback
            error_data = {
                "type": "error", 
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            yield json.dumps(error_data, ensure_ascii=False) + "\n"

    return StreamingResponse(generator(), media_type="text/plain")


@app.get("/")
async def root():
    return {"status": "ok", "framework": "Microsoft Agent Framework"}

if __name__ == "__main__":
    import uvicorn
    print("=== Agent Framework (Workflow Edition) Backend Starting ===")
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("\nCtrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
