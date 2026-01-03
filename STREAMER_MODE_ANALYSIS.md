# AI Streamer Mode (Passive Reaction) 구현 가이드

AI가 사용자의 직접적인 입력 없이도, 방송 화면(Stream)을 계속 지켜보면서 스스로 리액션하는 "Streamer Mode"를 구현하기 위한 분석 리포트입니다.

## 1. 구현 목표
*   **Frontend**: 1초(또는 N초) 간격으로 현재 화면을 캡처하여 서버로 전송.
*   **Backend**: 수신된 이미지를 처리하되, 사용자가 말하고 있거나 AI가 이미 말하고 있는 중이라면 방해하지 않음.
*   **AI Logic**: 별일 없으면 무시(PASS)하고, 반응할 만한 상황에서만 발화.

## 2. 변경해야 할 구성 요소

### 2.1 Frontend (React / Web Tool)
현재 프론트엔드(`index.js` 또는 `main.js`)에 타이머 루프를 추가해야 합니다.
**주의**: 1초마다 고화질 이미지를 보내면 토큰 비용이 폭발하고 서버 큐가 막힙니다. 해상도를 낮추거나 전송 주기를 3~5초로 조정하는 것을 권장합니다.

```javascript
// (예시 개념 코드)
setInterval(async () => {
    if (isStreamerModeOn && !isUserTalking && !isAITalking) {
        const image = await captureScreen(); // Base64
        websocket.send(JSON.stringify({
            type: "passive-vision-update", // 새로운 메시지 타입
            images: [{ source: "screen", data: image, mime_type: "image/jpeg" }]
        }));
    }
}, 5000); // 5초 주기 권장
```

### 2.2 Backend - WebSocket Router (`websocket_handler.py`)
새로운 메시지 타입 `passive-vision-update`를 처리할 핸들러를 등록해야 합니다.

**변경 파일**: `src/open_llm_vtuber/websocket_handler.py`

```python
# _init_message_handlers 메서드에 추가
"passive-vision-update": self._handle_passive_vision
```

**새로운 핸들러 메서드 추가**:
```python
async def _handle_passive_vision(self, websocket: WebSocket, client_uid: str, data: WSMessage):
    # 1. 현재 대화가 진행 중인지 확인 (Lock)
    if self.current_conversation_tasks.get(client_uid) and not self.current_conversation_tasks[client_uid].done():
        # 이미 말하고 있거나 듣고 있으면 시각 정보 무시 (또는 최신 프레임만 버퍼에 저장)
        return

    # 2. 대화 로직 실행 (flag: passive=True)
    # 기존 handle_conversation_trigger와 유사하지만, "무시(PASS)" 로직이 포함된 함수 호출
    await handle_passive_conversation(..., data=data)
```

### 2.3 Backend - Conversation Logic (`conversation_handler.py` & `single_conversation.py`)
"Passive Conversation"은 기존 대화와 다르게 **"말 안 하기"**라는 선택지가 있어야 합니다.

1.  **System Prompt 수정**: `agent`에게 보낼 시스템 프롬프트에 "특별한 일이 없으면 `<PASS>`라고만 출력해라"라는 지침을 추가해야 합니다.
2.  **Output 필터링**: `agent_engine.chat()`의 결과가 `<PASS>`라면 아무것도 하지 않고 함수를 종료합니다.

```python
# (개념 코드)
async def process_passive_conversation(...):
    # ... (기본 설정)
    
    # Vision 용 프롬프트 추가
    system_instruction = "You are watching a stream. Describe only noteworthy events. If boring, output <PASS>."
    
    # Agent 호출
    full_response = ""
    async for output in agent_engine.chat(batch_input):
        if output.text == "<PASS>":
            return # 아무 리액션 안함
        full_response += output.text
        # ... (TTS 및 전송 로직)
```

### 3. 기술적 난관 및 해결 방안 (Trade-offs)

1.  **비용 (Cost)**
    *   **문제**: GPT-4o에 5초마다 이미지를 보내면 분당 12회, 시간당 720회 요청입니다. 비용이 매우 많이 발생합니다.
    *   **해결**: 
        *   `gpt-4o-mini` 같은 저렴한 비전 모델을 사용하여 1차 필터링("재밌는 상황인가?" T/F 판별)을 거친 후, True일 때만 메인 모델 호출.
        *   이미지 해상도를 512px 이하로 축소.

2.  **지연 시간 (Latency)**
    *   **문제**: 이미지를 분석하고 리랙션 생성까지 1~2초가 걸리면, 이미 상황이 지났을 수 있습니다.
    *   **해결**: "패스트 트랙"을 위해 리액션(감탄사 등)을 먼저 뱉고(TTS), 상세 설명은 뒤에 붙이는 프롬프트 전략 사용.

3.  **사용자 입력 충돌**
    *   **문제**: AI가 혼자 떠들고 있을 때 사용자가 말을 걸면?
    *   **해결**: `handle_interrupt` 로직은 이미 구현되어 있으므로, 사용자가 말을 시작하면(`mic-audio-start`) 즉시 현재의 Vision 패시브 태스크를 `cancel()` 시키면 됩니다.

## 4. 요약
구현을 위해서는 **Backend의 WebSocket 핸들러에 `passive-vision-update`를 추가**하고, **Frontend에서 주기적으로 이미지를 쏘는 루프**를 만들어야 합니다. 가장 중요한 것은 **돈**과 **응답 속도** 밸런스를 맞추는 것입니다.
