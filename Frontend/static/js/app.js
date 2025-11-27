// グローバル変数
let isBusy = false;
let isMultiAgent = false;
let messages = [];
const sessionId = 'default';

// DOM要素
const chatMessages = document.getElementById('chatMessages');
const welcomeScreen = document.getElementById('welcomeScreen');
const promptInput = document.getElementById('promptInput');
const sendButton = document.getElementById('sendButton');
const multiAgentButton = document.getElementById('multiAgentButton');
const clearButton = document.getElementById('clearButton');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');

// イベントリスナーの設定
promptInput.addEventListener('input', updateButtons);
promptInput.addEventListener('keydown', handleKeyDown);
sendButton.addEventListener('click', () => startChat(false));
multiAgentButton.addEventListener('click', () => startChat(true));
clearButton.addEventListener('click', clearChat);

// 初期化
updateButtons();

function updateButtons() {
    const hasText = promptInput.value.trim().length > 0;
    sendButton.disabled = isBusy || !hasText;
    multiAgentButton.disabled = isBusy || !hasText;
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey && !isBusy) {
        event.preventDefault();
        startChat(false);
    }
}

function setPrompt(text) {
    promptInput.value = text;
    promptInput.focus();
    updateButtons();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatTime(date) {
    return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
}

function hideWelcomeScreen() {
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
    clearButton.style.display = 'block';
}

function showWelcomeScreen() {
    if (messages.length === 0) {
        if (welcomeScreen) {
            welcomeScreen.style.display = 'flex';
        }
        clearButton.style.display = 'none';
    }
}

function addUserMessage(content, isMultiAgentMode = false) {
    const timestamp = new Date();
    const message = {
        is_user: true,
        content: isMultiAgentMode ? `🔀 [マルチエージェント分析] ${content}` : content,
        timestamp: timestamp
    };
    messages.push(message);
    renderMessage(message);
    hideWelcomeScreen();
    scrollToBottom();
}

function addAiMessage(isMultiAgentMode = false) {
    const timestamp = new Date();
    const message = {
        is_user: false,
        content: '',
        timestamp: timestamp,
        is_streaming: true,
        is_multi_agent: isMultiAgentMode,
        critical_content: '',
        positive_content: '',
        synthesis_content: '',
        critical_streaming: isMultiAgentMode,
        positive_streaming: isMultiAgentMode,
        synthesis_streaming: false,
        element: null
    };
    messages.push(message);
    renderMessage(message);
    scrollToBottom();
    return message;
}

function renderMessage(message) {
    if (message.is_multi_agent) {
        renderMultiAgentMessage(message);
    } else {
        renderNormalMessage(message);
    }
}

function renderNormalMessage(message) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${message.is_user ? 'user-wrapper' : 'ai-wrapper'}`;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.is_user ? 'user-message' : 'ai-message'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = `<span class="avatar-icon">${message.is_user ? '👤' : '🤖'}</span>`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    header.innerHTML = `
        <strong>${message.is_user ? 'あなた' : 'AI アシスタント'}</strong>
        <span class="message-time">${formatTime(message.timestamp)}</span>
    `;
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = message.content;
    
    if (message.is_streaming) {
        const indicator = document.createElement('span');
        indicator.className = 'typing-indicator';
        indicator.textContent = '▊';
        textDiv.appendChild(indicator);
    }
    
    contentDiv.appendChild(header);
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    wrapper.appendChild(messageDiv);
    chatMessages.appendChild(wrapper);
    
    message.element = textDiv;
}

function renderMultiAgentMessage(message) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper ai-wrapper';
    
    const container = document.createElement('div');
    container.className = 'multi-agent-container';
    
    const header = document.createElement('div');
    header.className = 'multi-agent-header';
    header.innerHTML = `
        <span class="multi-agent-icon">🔀</span>
        <strong>マルチエージェント分析</strong>
        <span class="message-time">${formatTime(message.timestamp)}</span>
    `;
    
    const grid = document.createElement('div');
    grid.className = 'agents-grid';
    
    // 批判的視点パネル
    const criticalPanel = document.createElement('div');
    criticalPanel.className = 'agent-panel critical-panel';
    criticalPanel.innerHTML = `
        <div class="agent-panel-header">
            <span class="agent-icon">🔍</span>
            <span class="agent-title">批判的視点</span>
        </div>
        <div class="agent-content" data-agent="critical"></div>
    `;
    
    // 肯定的視点パネル
    const positivePanel = document.createElement('div');
    positivePanel.className = 'agent-panel positive-panel';
    positivePanel.innerHTML = `
        <div class="agent-panel-header">
            <span class="agent-icon">✨</span>
            <span class="agent-title">肯定的視点</span>
        </div>
        <div class="agent-content" data-agent="positive"></div>
    `;
    
    grid.appendChild(criticalPanel);
    grid.appendChild(positivePanel);
    
    // 統合分析パネル
    const synthesisPanel = document.createElement('div');
    synthesisPanel.className = 'synthesis-panel';
    synthesisPanel.style.display = 'none';
    synthesisPanel.innerHTML = `
        <div class="synthesis-header">
            <span class="synthesis-icon">🎯</span>
            <span class="synthesis-title">統合分析</span>
        </div>
        <div class="synthesis-content" data-agent="synthesis"></div>
    `;
    
    container.appendChild(header);
    container.appendChild(grid);
    container.appendChild(synthesisPanel);
    wrapper.appendChild(container);
    chatMessages.appendChild(wrapper);
    
    message.element = {
        critical: criticalPanel.querySelector('[data-agent="critical"]'),
        positive: positivePanel.querySelector('[data-agent="positive"]'),
        synthesis: synthesisPanel.querySelector('[data-agent="synthesis"]'),
        synthesisPanel: synthesisPanel
    };
}

function updateMessageContent(message, content) {
    if (message.is_multi_agent) {
        // マルチエージェントメッセージは別途処理
        return;
    }
    
    message.content = content;
    if (message.element) {
        message.element.textContent = content;
        
        if (message.is_streaming) {
            const indicator = document.createElement('span');
            indicator.className = 'typing-indicator';
            indicator.textContent = '▊';
            message.element.appendChild(indicator);
        }
    }
}

function updateMultiAgentContent(message, agent, content) {
    if (!message.element) return;
    
    if (agent === 'CriticalAnalyst') {
        message.critical_content += content;
        message.element.critical.textContent = message.critical_content;
    } else if (agent === 'PositiveAdvocate') {
        message.positive_content += content;
        message.element.positive.textContent = message.positive_content;
    } else if (agent === 'Synthesizer') {
        message.synthesis_content += content;
        message.element.synthesis.textContent = message.synthesis_content;
        message.element.synthesisPanel.style.display = 'block';
    }
}

function setStatus(busy, multiAgent = false) {
    isBusy = busy;
    isMultiAgent = multiAgent;
    
    promptInput.disabled = busy;
    updateButtons();
    
    if (busy) {
        statusIndicator.style.display = 'flex';
        statusText.textContent = multiAgent ? 'マルチエージェント分析中...' : 'AI が考え中...';
        
        // ボタンのアイコンを変更
        if (multiAgent) {
            multiAgentButton.innerHTML = '<span class="spinner-icon">⟳</span>';
        } else {
            sendButton.innerHTML = '<span class="spinner-icon">⟳</span>';
        }
    } else {
        statusIndicator.style.display = 'none';
        sendButton.innerHTML = '<span class="send-icon">📤</span>';
        multiAgentButton.innerHTML = '<span class="multi-agent-icon">🔀</span>';
    }
}

async function startChat(multiAgent = false) {
    const prompt = promptInput.value.trim();
    if (!prompt || isBusy) return;
    
    promptInput.value = '';
    updateButtons();
    
    addUserMessage(prompt, multiAgent);
    const aiMessage = addAiMessage(multiAgent);
    
    setStatus(true, multiAgent);
    
    try {
        if (multiAgent) {
            await streamMultiAgentChat(prompt, aiMessage);
        } else {
            await streamNormalChat(prompt, aiMessage);
        }
    } catch (error) {
        const errorMsg = `\n\n❌ エラー: ${error.message}`;
        if (multiAgent) {
            aiMessage.synthesis_content = errorMsg;
            updateMultiAgentContent(aiMessage, 'Synthesizer', errorMsg);
        } else {
            updateMessageContent(aiMessage, aiMessage.content + errorMsg);
        }
    } finally {
        aiMessage.is_streaming = false;
        aiMessage.critical_streaming = false;
        aiMessage.positive_streaming = false;
        aiMessage.synthesis_streaming = false;
        setStatus(false);
    }
}

async function streamNormalChat(prompt, aiMessage) {
    const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, session_id: sessionId })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        aiMessage.content += chunk;
        updateMessageContent(aiMessage, aiMessage.content);
        scrollToBottom();
    }
}

async function streamMultiAgentChat(prompt, aiMessage) {
    const response = await fetch('/api/chat/multi-agent-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, session_id: sessionId })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
            if (line.trim()) {
                try {
                    const data = JSON.parse(line);
                    
                    if (data.type === 'synthesis_start') {
                        aiMessage.synthesis_streaming = true;
                    } else if (data.agent && data.content) {
                        updateMultiAgentContent(aiMessage, data.agent, data.content);
                        scrollToBottom();
                    }
                } catch (e) {
                    console.error('JSON parse error:', e);
                }
            }
        }
    }
}

function clearChat() {
    if (!confirm('チャット履歴をクリアしますか？')) return;
    
    fetch('/api/messages/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
    });
    
    messages = [];
    chatMessages.innerHTML = '';
    showWelcomeScreen();
}
