import requests
import os
from datetime import datetime
api_key = os.getenv("ELEVENLABS_API_KEY") 
url = "https://api.elevenlabs.io/v1/text-to-speech/uyVNoMrnUku1dZyVEXwD"
params = {
    "output_format": "mp3_44100_128"
}
headers = {
    "xi-api-key": api_key,
    "Content-Type": "application/json"
}


# 태그리스트 공식문서 : https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices#targeted-niche 
# Audio Tags Dictionary (Eleven v3)
AUDIO_TAGS = {
    # Voice-related
    "laughs": "[laughs]",
    "laughs_harder": "[laughs harder]",
    "starts_laughing": "[starts laughing]",
    "wheezing": "[wheezing]",
    "whispers": "[whispers]",
    "sighs": "[sighs]",
    "exhales": "[exhales]",
    "sarcastic": "[sarcastic]",
    "curious": "[curious]",
    "excited": "[excited]",
    "crying": "[crying]",
    "snorts": "[snorts]",
    "mischievously": "[mischievously]",
    
    # Sound effects 도 커스텀으로 생성할 수 있음
    # Sound effects 라이브러리 : https://elevenlabs.io/app/sound-effects
    "gunshot": "[gunshot]",
    "applause": "[applause]",
    "clapping": "[clapping]",
    "explosion": "[explosion]",
    "swallows": "[swallows]",
    "gulps": "[gulps]",
    
    # Unique and special
    "sings": "[sings]",
    "woo": "[woo]",
    "fart": "[fart]",
    "strong_french_accent": "[strong French accent]",
}

def generate_tts(text, output_filename="output.mp3"):
    data = {
        "text": text,
        "model_id": "eleven_v3"
    }

    # 2. 요청 보내기
    print(f"Requesting to: {url}")
    # SSL 인증서 문제 우회를 위해 verify=False 설정 및 경고 숨기기
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(url, json=data, headers=headers, params=params, verify=False)

    # 3. 결과 확인
    if response.status_code == 200:
        print("성공! mp3 파일로 저장합니다.")
        with open(output_filename, "wb") as f:
            f.write(response.content)
        print(f"저장 완료: {output_filename}")
    else:
        print(f"실패: {response.status_code}")
        print(response.text)

# 실행 예시
if __name__ == "__main__":
    # 바꿀 감정 앞에 오디오태그 명 추가시, 적용
    text_input = f"{AUDIO_TAGS['laughs']}와 이거.. {AUDIO_TAGS['gunshot']}정말 배고프겠는데... {AUDIO_TAGS['laughs_harder']}하하하하하하"
    
    # 현재 시간으로 파일명 생성 (예: tts_20241226_180000.mp3)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tts_{current_time}.mp3"
    
    generate_tts(text_input, filename)