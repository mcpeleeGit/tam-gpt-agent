# MCP 서버 (Model Context Protocol)

## 개요

MCP 서버는 GPT 에이전트가 외부 서비스(카카오톡 등)와 통신할 수 있도록 하는 프로토콜 서버입니다.

## tam-admin 서버 (신규)

### 설치 및 실행

```bash
cd mcp_server
python3 tam_admin_mcp_server.py
```

기본 포트: `5005`

환경 변수 설정 (`.env`):
```
TAM_ADMIN_MCP_SERVER_PORT=5005
TAM_ADMIN_API_BASE_URL=https://tam-admin.example.com  # (스펙 확정 전, 선택)
```

### API 엔드포인트

#### 1. 헬스 체크
```
GET /mcp/tam-admin/health

Response:
{
  "status": "healthy",
  "service": "tam_admin_mcp_server",
  "version": "1.0.0"
}
```

#### 2. 기능 목록 조회
```
GET /mcp/tam-admin/capabilities

Response:
{
  "tools": [
    {
      "name": "tam_admin_action",
      "description": "tam-admin API 제너릭 액션 프록시",
      "parameters": {"action": "string", "payload": "object", "method": "string"}
    }
  ]
}
```

#### 3. 제너릭 프록시 (스펙 확정 전)
```
POST /mcp/tam-admin/proxy

Request Body 예:
{
  "action": "get_customer",
  "payload": { ... },
  "method": "POST"
}

Response: 501 Not Implemented (스펙 확정 전)
```

## 카카오톡 메시지 발송 서버

### 설치 및 실행

```bash
cd mcp_server
python3 kakao_mcp_server.py
```

기본 포트: `5003`

환경 변수 설정 (`.env`):
```
MCP_SERVER_PORT=5003
KAKAO_API_BASE_URL=https://kapi.kakao.com
KAKAO_REST_API_KEY=your_kakao_rest_api_key
```

### API 엔드포인트

#### 1. 카카오톡 메시지 발송
```
POST /mcp/kakao/send

Request Body:
{
    "receiver_id": "user123",
    "message": "안녕하세요",
    "template_id": null  // optional
}

Response:
{
    "success": true,
    "message_id": "msg_123456",
    "receiver_id": "user123",
    "message": "안녕하세요",
    "sent_at": "2024-10-26T15:00:00Z",
    "status": "sent"
}
```

#### 2. 헬스 체크
```
GET /mcp/kakao/health

Response:
{
    "status": "healthy",
    "service": "kakao_mcp_server",
    "version": "1.0.0"
}
```

#### 3. 기능 목록 조회
```
GET /mcp/kakao/capabilities

Response:
{
    "tools": [...]
}
```

## 현재 상태

- ✅ 기본 구조 구현 완료
- ✅ 카카오톡 API 호출 로직 구현 완료

## 환경 변수 설정

`.env` 파일에 다음을 추가하세요:

```
KAKAO_ACCESS_TOKEN=your_kakao_access_token
MCP_SERVER_PORT=5003
```

## API 스펙

카카오톡 API 사용:
- 엔드포인트: `POST https://kapi.kakao.com/v2/api/talk/memo/default/send`
- 인증: Bearer Token (ACCESS_TOKEN)
- Content-Type: `application/x-www-form-urlencoded;charset=utf-8`

## 구현 완료

1. ✅ `KakaoMessenger.send_message()` - 실제 카카오톡 API 호출
2. ✅ 에러 처리 및 타임아웃 처리
3. ✅ 메시지 길이 제한 (200자)
4. ⏳ 템플릿 메시지 (필요시 추가 구현)

## 주의사항

- ACCESS_TOKEN은 카카오 개발자 콘솔에서 발급받아야 합니다
- 현재 API는 로그인한 사용자의 친구들에게 메시지를 보내는 형태입니다
- receiver_uuids 파라미터가 필요한 경우 추가 구현이 필요할 수 있습니다

