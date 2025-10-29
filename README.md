# Flask AI 채팅 어시스턴트

OpenAI GPT-3.5-turbo를 사용한 웹 기반 채팅 어시스턴트입니다.

## 기능

- 실시간 AI 채팅
- 채팅 기록 저장 및 불러오기
- 반응형 웹 디자인
- 채팅 기록 삭제 기능
- 로딩 인디케이터

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

### 3. 애플리케이션 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000`으로 접속하세요.

## 프로젝트 구조

```
agent/
├── app.py                 # Flask 메인 애플리케이션
├── requirements.txt       # Python 의존성
├── templates/
│   └── index.html        # 메인 HTML 템플릿
└── static/
    ├── css/
    │   └── style.css     # 스타일시트
    └── js/
        └── script.js     # JavaScript 로직
```

## API 엔드포인트

- `GET /` - 메인 페이지
- `POST /chat` - 채팅 메시지 전송
- `POST /clear` - 채팅 기록 삭제
- `GET /history` - 채팅 기록 조회

## 사용된 기술

- **Backend**: Flask, OpenAI API
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: CSS Grid, Flexbox, CSS Animations
- **Icons**: Font Awesome

## 주의사항

- OpenAI API 키를 안전하게 관리하세요
- 프로덕션 환경에서는 환경 변수를 통해 API 키를 설정하세요
- API 사용량에 따른 비용이 발생할 수 있습니다
