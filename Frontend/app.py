from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import httpx
import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator
import os

app = Flask(__name__)
app.config['BACKEND_URL'] = os.getenv('BACKEND_URL', 'http://localhost:8000')

# セッションストレージ（実運用ではRedisなどを使用）
messages_store = {}


@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/api/messages', methods=['GET'])
def get_messages():
    """メッセージ履歴を取得"""
    session_id = request.args.get('session_id', 'default')
    messages = messages_store.get(session_id, [])
    return jsonify(messages)


@app.route('/api/messages/clear', methods=['POST'])
def clear_messages():
    """メッセージ履歴をクリア"""
    data = request.json
    session_id = data.get('session_id', 'default')
    messages_store[session_id] = []
    return jsonify({'status': 'ok'})


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """通常チャットのストリーミング"""
    data = request.json
    prompt = data.get('prompt', '')
    session_id = data.get('session_id', 'default')
    
    if not prompt:
        return jsonify({'error': 'prompt required'}), 400
    
    # ユーザーメッセージを保存
    if session_id not in messages_store:
        messages_store[session_id] = []
    
    user_message = {
        'is_user': True,
        'content': prompt,
        'timestamp': datetime.now().isoformat()
    }
    messages_store[session_id].append(user_message)
    
    def generate():
        """ストリーミングレスポンスを生成"""
        ai_content = ""
        try:
            with httpx.Client(timeout=60.0) as client:
                with client.stream(
                    'POST',
                    f"{app.config['BACKEND_URL']}/api/stream",
                    json={'prompt': prompt}
                ) as response:
                    response.raise_for_status()
                    for chunk in response.iter_text():
                        if chunk:
                            ai_content += chunk
                            yield chunk
            
            # AIメッセージを保存
            ai_message = {
                'is_user': False,
                'content': ai_content,
                'timestamp': datetime.now().isoformat(),
                'is_streaming': False
            }
            messages_store[session_id].append(ai_message)
            
        except Exception as e:
            error_msg = f"\n\n❌ エラー: {str(e)}"
            yield error_msg
            
            ai_message = {
                'is_user': False,
                'content': ai_content + error_msg,
                'timestamp': datetime.now().isoformat(),
                'is_streaming': False
            }
            messages_store[session_id].append(ai_message)
    
    return Response(stream_with_context(generate()), content_type='text/plain')


@app.route('/api/chat/multi-agent-stream', methods=['POST'])
def multi_agent_stream():
    """マルチエージェントチャットのストリーミング"""
    data = request.json
    prompt = data.get('prompt', '')
    session_id = data.get('session_id', 'default')
    
    if not prompt:
        return jsonify({'error': 'prompt required'}), 400
    
    # ユーザーメッセージを保存
    if session_id not in messages_store:
        messages_store[session_id] = []
    
    user_message = {
        'is_user': True,
        'content': f"🔀 [マルチエージェント分析] {prompt}",
        'timestamp': datetime.now().isoformat()
    }
    messages_store[session_id].append(user_message)
    
    def generate():
        """マルチエージェントストリーミングレスポンスを生成"""
        ai_message = {
            'is_user': False,
            'is_multi_agent': True,
            'timestamp': datetime.now().isoformat(),
            'critical_content': '',
            'positive_content': '',
            'synthesis_content': ''
        }
        
        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream(
                    'POST',
                    f"{app.config['BACKEND_URL']}/api/multi-agent-stream",
                    json={'prompt': prompt}
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line.strip():
                            try:
                                # JSON-Lines形式で送信
                                yield line + '\n'
                                
                                # メッセージストアを更新
                                data = json.loads(line)
                                if 'agent' in data and 'content' in data:
                                    agent = data['agent']
                                    content = data['content']
                                    
                                    if agent == 'CriticalAnalyst':
                                        ai_message['critical_content'] += content
                                    elif agent == 'PositiveAdvocate':
                                        ai_message['positive_content'] += content
                                    elif agent == 'Synthesizer':
                                        ai_message['synthesis_content'] += content
                            except json.JSONDecodeError:
                                continue
            
            # AIメッセージを保存
            messages_store[session_id].append(ai_message)
            
        except Exception as e:
            error_data = {'type': 'error', 'message': str(e)}
            yield json.dumps(error_data) + '\n'
            
            ai_message['synthesis_content'] = f"❌ エラー: {str(e)}"
            messages_store[session_id].append(ai_message)
    
    return Response(stream_with_context(generate()), content_type='text/plain')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
