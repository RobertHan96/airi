# Open-LLM-VTuber Vision 프로세스 분석 보고서

이 문서는 Open-LLM-VTuber 프로젝트에서 시각 정보(Vision, 화면 캡처 또는 이미지)가 처리되는 과정을 분석한 보고서입니다.

## 1. 개요 (Overview)

이 프로젝트의 Vision 기능은 자체적인 컴퓨터 비전(Computer Vision) 모델을 사용하는 것이 아니라, **Multimodal LLM(예: GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro 등)**의 시각 처리 능력에 의존합니다. 프론트엔드에서 캡처한 이미지를 Base64 형태로 백엔드로 전송하면, 백엔드는 이를 OpenAI 호환 API 포맷(`image_url`)으로 변환하여 LLM에게 전달하는 방식을 사용합니다.

## 2. 데이터 처리 흐름 (Data Flow)

전체적인 데이터 흐름은 다음과 같습니다.

1.  **Client (Frontend)**: 화면이나 카메라를 캡처하여 이미지를 생성하고, 이를 Base64 인코딩된 문자열(`data:image/...`)로 변환합니다. WebSocket 메시지의 `images` 필드에 담아 서버로 전송합니다.
2.  **WebSocket Server**: 클라이언트로부터 메시지를 수신하고 분류합니다.
3.  **Conversation Handler**: 대화 처리 로직으로 이미지를 전달합니다.
4.  **Agent Engine**: 수신된 이미지를 LLM이 이해할 수 있는 메시지 포맷으로 변환하고 API 요청을 보냅니다.
5.  **LLM Provider**: 이미지를 분석하고 그에 대한 텍스트 응답을 생성하여 반환합니다.

## 3. 상세 코드 분석 (Code Analysis)

### 3.1 WebSocket 핸들러 (Router)
*   **파일**: `src/open_llm_vtuber/websocket_handler.py`
*   **역할**: 클라이언트로부터 들어오는 JSON 메시지를 파싱합니다. `WSMessage` 타입 정의를 보면 `images` 필드가 포함되어 있습니다.

```python
class WSMessage(TypedDict, total=False):
    # ...
    images: Optional[List[str]]  # 이미지 데이터 리스트
    # ...
```

*   `handle_conversation_trigger` 메서드를 통해 대화 처리 흐름을 시작합니다.

### 3.2 대화 처리 (Conversation Handler)
*   **파일**: `src/open_llm_vtuber/conversations/conversation_handler.py`
*   **파일**: `src/open_llm_vtuber/conversations/single_conversation.py`
*   **역할**: 수신된 데이터를 `images` 변수로 추출하고, `process_single_conversation` 함수로 전달합니다.

```python
# conversation_handler.py
images = data.get("images")
# ...
process_single_conversation(..., images=images, ...)
```

`process_single_conversation`에서는 `create_batch_input` 유틸리티를 사용하여 텍스트와 이미지를 하나의 `BatchInput` 객체로 묶습니다.

```python
# single_conversation.py
batch_input = create_batch_input(
    input_text=input_text,
    images=images,
    # ...
)
agent_output_stream = context.agent_engine.chat(batch_input)
```

### 3.3 데이터 구조 (Data Structures)
*   **파일**: `src/open_llm_vtuber/conversations/conversation_utils.py`
*   **파일**: `src/open_llm_vtuber/agent/input_types.py`
*   **역할**: Raw 이미지 데이터를 내부 데이터 구조인 `ImageData` 및 `BatchInput`으로 변환합니다.

```python
# conversation_utils.py
def create_batch_input(..., images, ...) -> BatchInput:
    return BatchInput(
        # ...
        images=[
            ImageData(
                source=ImageSource(img["source"]), 
                data=img["data"],  # Base64 string
                mime_type=img["mime_type"],
            )
            for img in (images or [])
        ]
        # ...
    )
```

### 3.4 에이전트 및 LLM 연동 (Agent & LLM Integration)
*   **파일**: `src/open_llm_vtuber/agent/agents/basic_memory_agent.py`
*   **역할**: `BatchInput`을 받아 실제 LLM API에 보낼 메시지 포맷(`messages` list)으로 변환합니다. 여기서 중요한 점은 이미지를 `image_url` 타입의 메시지로 변환한다는 것입니다.

```python
# basic_memory_agent.py - _to_messages 메서드
if input_data.images:
    for img_data in input_data.images:
        if isinstance(img_data.data, str) and img_data.data.startswith("data:image"):
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": img_data.data, "detail": "auto"},
                }
            )
```

이렇게 변환된 `messages` 리스트는 `self._llm.chat_completion`을 통해 설정된 LLM(OpenAI, Claude 등)으로 전송됩니다.

## 4. 결론 (Conclusion)

Open-LLM-VTuber의 "Vision" 기능은 복잡한 이미지 처리 파이프라인을 내장하고 있지 않습니다. 대신, **"이미지를 텍스트와 함께 LLM에게 보여주고 답변을 얻는"** 방식을 취하고 있습니다.

따라서 이 기능이 제대로 작동하려면 다음 조건이 충족되어야 합니다:
1.  **Frontend**: 이미지를 캡처하여 Base64로 잘 변환해서 보내줘야 함.
2.  **Config**: `conf.yaml`에서 설정된 LLM 모델이 이미지 입력을 지원하는 **Multimodal Model**이어야 함 (예: `gpt-4o`, `claude-3-5-sonnet`, `gemini-1.5-pro` 등). 텍스트 전용 모델을 사용하면 에러가 발생하거나 이미지를 무시할 것입니다.
