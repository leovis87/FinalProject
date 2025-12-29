from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional
import anthropic
import os

app = FastAPI()

# Claude API 클라이언트 생성
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# Claude 모델 설정
models = {
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
    "opus": "claude-opus-4-20250514"
}

# 대화 히스토리 저장
conversation: List[Dict] = []

def set_prompt(role: str, content: str) -> Dict:
    """
    API에게 prompt를 주입하기 위한 메시지 구조 생성
    """
    return {
        "role": role,
        "content": content
    }

# Request 모델들
class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "haiku"

class SystemPromptRequest(BaseModel):
    system_prompt: str

@app.get("/", response_class=HTMLResponse)
async def index():
    """메인 페이지"""
    html_content = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name = "viewport" content = "width=device-width, initial-scale=1.0">
    <title>Claude Chat MVP</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .container {
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .header h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }

        .controls {
            display: flex;
            gap: 10px;
            justify-content: center;
            align-items: center;
            margin-top: 10px;
        }

        .controls select, .controls button {
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }

        .controls select {
            background: white;
            color: #667eea;
        }

        .controls button {
            background: rgba(255,255,255,0.2);
            color: white;
            transition: background 0.3s;
        }

        .controls button:hover {
            background: rgba(255,255,255,0.3);
        }

        .chat-box {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }

        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            justify-content: flex-end;
        }

        .message-content {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .message.assistant .message-content {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .system-prompt-area {
            margin-bottom: 10px;
        }

        .system-prompt-area textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #667eea;
            border-radius: 10px;
            resize: vertical;
            font-size: 14px;
            min-height: 60px;
        }

        .system-prompt-area button {
            margin-top: 5px;
            padding: 8px 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }

        .system-prompt-area button:hover {
            background: #5568d3;
        }

        .input-box {
            display: flex;
            gap: 10px;
        }

        .input-box input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        .input-box input:focus {
            outline: none;
            border-color: #667eea;
        }

        .input-box button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
        }

        .input-box button:hover {
            transform: scale(1.05);
        }

        .input-box button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: scale(1);
        }

        .loading {
            display: none;
            text-align: center;
            color: #667eea;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Claude Chat MVP</h1>
            <div class="controls">
                <select id="modelSelect">
                    <option value="haiku">Haiku (Fast & Cheap)</option>
                    <option value="sonnet" selected>Sonnet (Balanced)</option>
                    <option value="opus">Opus (Most Capable)</option>
                </select>
                <button onclick="clearChat()">Clear Chat</button>
            </div>
        </div>

        <div class="chat-box" id="chatBox"></div>

        <div class="loading" id="loading">
            <p>Claude is thinking...</p>
        </div>

        <div class="input-area">
            <div class="system-prompt-area">
                <textarea id="systemPrompt" placeholder="System Prompt (Optional): Set the role and behavior of Claude..."></textarea>
                <button onclick="setSystemPrompt()">Set System Prompt</button>
            </div>
            <div class="input-box">
                <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" id="sendButton">Send</button>
            </div>
        </div>
    </div>

    <script>
        const chatBox = document.getElementById('chatBox');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loading = document.getElementById('loading');
        const modelSelect = document.getElementById('modelSelect');
        const systemPrompt = document.getElementById('systemPrompt');

        function addMessage(role, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;

            messageDiv.appendChild(contentDiv);
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            const model = modelSelect.value;

            // Add user message to chat
            addMessage('user', message);
            messageInput.value = '';

            // Disable input while processing
            sendButton.disabled = true;
            messageInput.disabled = true;
            loading.style.display = 'block';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        model: model
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    addMessage('assistant', data.response);
                } else {
                    addMessage('assistant', `Error: ${data.error}`);
                }
            } catch (error) {
                addMessage('assistant', `Error: ${error.message}`);
            } finally {
                sendButton.disabled = false;
                messageInput.disabled = false;
                loading.style.display = 'none';
                messageInput.focus();
            }
        }

        async function clearChat() {
            try {
                await fetch('/clear', { method: 'POST' });
                chatBox.innerHTML = '';
                systemPrompt.value = '';
            } catch (error) {
                console.error('Clear failed:', error);
            }
        }

        async function setSystemPrompt() {
            const prompt = systemPrompt.value.trim();
            if (!prompt) {
                alert('Please enter a system prompt');
                return;
            }

            loading.style.display = 'block';
            sendButton.disabled = true;

            try {
                const response = await fetch('/set_system_prompt', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        system_prompt: prompt
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    chatBox.innerHTML = '';
                    addMessage('user', `[SYSTEM] ${prompt}`);
                    if (data.response) {
                        addMessage('assistant', data.response);
                    }
                    alert('System prompt set successfully!');
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                alert(`Error: ${error.message}`);
            } finally {
                loading.style.display = 'none';
                sendButton.disabled = false;
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        // Focus on input when page loads
        messageInput.focus();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/chat")
async def chat(request: ChatRequest):
    """채팅 API 엔드포인트"""
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="메시지를 입력해주세요")

        # 사용자 입력 추가
        conversation.append(set_prompt("user", request.message))

        # Claude API 호출
        response = client.messages.create(
            model=models.get(request.model, models['haiku']),
            max_tokens=2048,
            messages=conversation
        )

        # 응답 추출
        answer = response.content[0].text

        # conversation에 기록
        conversation.append(set_prompt("assistant", answer))

        return {
            "response": answer,
            "model": request.model
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear")
async def clear_conversation():
    """대화 히스토리 초기화"""
    global conversation
    conversation = []
    return {"status": "success"}

@app.post("/set_system_prompt")
async def set_system_prompt(request: SystemPromptRequest):
    """시스템 프롬프트 설정"""
    try:
        global conversation
        # 대화 초기화하고 시스템 프롬프트 설정
        conversation = []

        if request.system_prompt:
            # 시스템 프롬프트를 첫 사용자 메시지로 설정
            conversation.append(set_prompt("user", f"[SYSTEM] {request.system_prompt}"))

            # Claude에게 확인 응답 받기
            response = client.messages.create(
                model=models['sonnet'],
                max_tokens=512,
                messages=conversation
            )

            answer = response.content[0].text
            conversation.append(set_prompt("assistant", answer))

            return {"status": "success", "response": answer}

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
