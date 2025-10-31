"""
카카오톡 메시지 발송 MCP 서버
Model Context Protocol을 통해 GPT 에이전트가 카카오톡 메시지를 발송할 수 있도록 지원
"""
from flask import Flask, request, jsonify, redirect
import os
import json
import requests
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드 (mcp_server 디렉토리에서 실행되므로 상위 디렉토리 지정)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

# 카카오톡 API 설정
KAKAO_API_BASE_URL = os.getenv('KAKAO_API_BASE_URL', 'https://kapi.kakao.com')
KAKAO_API_ENDPOINT = f"{KAKAO_API_BASE_URL}/v2/api/talk/memo/default/send"
KAKAO_ACCESS_TOKEN = os.getenv('KAKAO_ACCESS_TOKEN', '')

# OAuth 설정 및 토큰 저장소
KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY', '')
# 콜백 미설정 시 기본값(현재 서버 포트 기준)
DEFAULT_REDIRECT_URI = f"http://127.0.0.1:{int(os.getenv('MCP_SERVER_PORT', 5003))}/mcp/kakao/oauth/callback"
KAKAO_REDIRECT_URI = os.getenv('KAKAO_REDIRECT_URI', DEFAULT_REDIRECT_URI)
KAKAO_SCOPES = os.getenv('KAKAO_SCOPES', 'talk_calendar')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_STORE_PATH = os.path.join(PROJECT_ROOT, 'data', 'kakao_tokens.json')

def load_tokens():
    try:
        if os.path.exists(TOKEN_STORE_PATH):
            with open(TOKEN_STORE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_tokens(tokens):
    try:
        os.makedirs(os.path.dirname(TOKEN_STORE_PATH), exist_ok=True)
        tokens['updated_at'] = datetime.now().isoformat()
        with open(TOKEN_STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def build_kakao_authorize_url(state=None):
    params = {
        'client_id': KAKAO_REST_API_KEY,
        'redirect_uri': KAKAO_REDIRECT_URI,
        'response_type': 'code',
        'scope': KAKAO_SCOPES,
    }
    if state:
        params['state'] = state
    return f"https://kauth.kakao.com/oauth/authorize?{urlencode(params)}"

def exchange_code_for_tokens(code):
    data = {
        'grant_type': 'authorization_code',
        'client_id': KAKAO_REST_API_KEY,
        'redirect_uri': KAKAO_REDIRECT_URI,
        'code': code,
    }
    resp = requests.post('https://kauth.kakao.com/oauth/token', data=data, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"토큰 교환 실패: {resp.status_code} {resp.text}")

def refresh_access_token(refresh_token):
    data = {
        'grant_type': 'refresh_token',
        'client_id': KAKAO_REST_API_KEY,
        'refresh_token': refresh_token,
    }
    resp = requests.post('https://kauth.kakao.com/oauth/token', data=data, timeout=10)
    if resp.status_code == 200:
        return resp.json()
    raise Exception(f"토큰 갱신 실패: {resp.status_code} {resp.text}")

class KakaoMessenger:
    """카카오톡 메시지 발송 클래스"""
    
    def __init__(self, access_token=None):
        tokens = load_tokens()
        self.access_token = access_token or tokens.get('access_token') or KAKAO_ACCESS_TOKEN
        self.api_endpoint = KAKAO_API_ENDPOINT
        self._last_auth_error = None

    def _update_access_token_from_store(self):
        tokens = load_tokens()
        new_token = tokens.get('access_token')
        if new_token:
            self.access_token = new_token

    def _attempt_refresh_and_update(self):
        tokens = load_tokens()
        refresh_token_value = tokens.get('refresh_token')
        if not (KAKAO_REST_API_KEY and refresh_token_value):
            return False
        try:
            refreshed = refresh_access_token(refresh_token_value)
            merged = {
                'access_token': refreshed.get('access_token', tokens.get('access_token')),
                'refresh_token': refreshed.get('refresh_token', tokens.get('refresh_token')),
                'token_type': refreshed.get('token_type', tokens.get('token_type')),
                'expires_in': refreshed.get('expires_in', tokens.get('expires_in')),
                'scope': refreshed.get('scope', tokens.get('scope')),
            }
            if save_tokens(merged):
                self._update_access_token_from_store()
                return True
        except Exception as e:
            self._last_auth_error = str(e)
        return False
    
    def send_message(self, message, web_url=None, mobile_web_url=None, button_title=None):
        """
        카카오톡 메시지 발송
        
        Args:
            message (str): 발송할 메시지 내용 (최대 200자)
            web_url (str, optional): 웹 URL 링크
            mobile_web_url (str, optional): 모바일 웹 URL 링크
            button_title (str, optional): 버튼 제목
        
        Returns:
            dict: 발송 결과
        """
        if not self.access_token:
            return {
                "success": False,
                "error": "KAKAO_ACCESS_TOKEN이 설정되지 않았습니다."
            }
        
        # 메시지가 200자 초과 시 잘라내기
        if len(message) > 200:
            message = message[:197] + "..."
        
        # template_object 구성
        template_object = {
            "object_type": "text",
            "text": message,
            "link": {}
        }
        
        # 링크 정보 추가 (제공된 경우)
        if web_url:
            template_object["link"]["web_url"] = web_url
        if mobile_web_url:
            template_object["link"]["mobile_web_url"] = mobile_web_url
        
        # 버튼 제목 추가
        if button_title:
            template_object["button_title"] = button_title
        
        # template_object를 JSON 문자열로 변환
        template_object_json = json.dumps(template_object, ensure_ascii=False)
        
        # URL 인코딩된 데이터 준비
        data = {
            'template_object': template_object_json
        }
        
        # 헤더 설정
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            print("[kakao_mcp_server] Messenger.send_message -> endpoint", self.api_endpoint, "payload:", data)
            # 카카오톡 API 호출
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                data=data,
                timeout=10
            )
            
            # 응답 확인
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": message,
                    "sent_at": datetime.now().isoformat(),
                    "status": "sent",
                    "api_response": result
                }
            elif response.status_code == 401:
                if self._attempt_refresh_and_update():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    retry_resp = requests.post(
                        self.api_endpoint,
                        headers=headers,
                        data=data,
                        timeout=10
                    )
                    if retry_resp.status_code == 200:
                        result = retry_resp.json()
                        return {
                            "success": True,
                            "message": message,
                            "sent_at": datetime.now().isoformat(),
                            "status": "sent",
                            "api_response": result,
                            "refreshed": True
                        }
                auth_url = build_kakao_authorize_url()
                return {
                    "success": False,
                    "error": "카카오톡 API 오류: 401",
                    "auth_required": True,
                    "auth_url": auth_url,
                    "provider": "kakao"
                }
            else:
                return {
                    "success": False,
                    "error": f"카카오톡 API 오류: {response.status_code}",
                    "error_message": response.text,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "카카오톡 API 호출 시간 초과"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"카카오톡 API 호출 실패: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"알 수 없는 오류: {str(e)}"
            }
    
    def send_template_message(self, receiver_id, template_id, template_args):
        """
        카카오톡 템플릿 메시지 발송
        
        Args:
            receiver_id (str): 수신자 ID
            template_id (str): 템플릿 ID
            template_args (dict): 템플릿 인자
        
        Returns:
            dict: 발송 결과
        """
        # TODO: 템플릿 메시지 API 호출 구현
        return {
            "success": True,
            "message_id": "msg_template_123456",
            "receiver_id": receiver_id,
            "template_id": template_id,
            "sent_at": "2024-10-26T15:00:00Z",
            "status": "sent"
        }

    def get_my_info(self):
        """카카오 사용자 정보 조회 (내정보)"""
        if not self.access_token:
            return {"success": False, "error": "KAKAO_ACCESS_TOKEN이 설정되지 않았습니다."}

        me_url = f"{os.getenv('KAKAO_API_BASE_URL', 'https://kapi.kakao.com')}/v2/user/me"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = requests.get(me_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 401:
                if self._attempt_refresh_and_update():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    retry_resp = requests.get(me_url, headers=headers, timeout=10)
                    if retry_resp.status_code == 200:
                        return {"success": True, "data": retry_resp.json(), "refreshed": True}
                return {"success": False, "error": "카카오톡 API 오류: 401", "auth_required": True, "auth_url": build_kakao_authorize_url(), "provider": "kakao"}
            else:
                return {
                    "success": False,
                    "error": f"카카오톡 API 오류: {response.status_code}",
                    "error_message": response.text,
                    "status_code": response.status_code
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "카카오톡 API 호출 시간 초과"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"카카오톡 API 호출 실패: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}

    def get_friends(self, offset=None, limit=None, order=None):
        """카카오톡 친구 목록 조회"""
        if not self.access_token:
            return {
                "success": False,
                "error": "KAKAO_ACCESS_TOKEN이 설정되지 않았습니다."
            }

        friends_url = f"{os.getenv('KAKAO_API_BASE_URL', 'https://kapi.kakao.com')}/v1/api/talk/friends"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {}
        if offset is not None:
            params['offset'] = offset
        if limit is not None:
            params['limit'] = limit
        if order is not None:
            params['order'] = order

        try:
            response = requests.get(friends_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data
                }
            elif response.status_code == 401:
                if self._attempt_refresh_and_update():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    retry_resp = requests.get(friends_url, headers=headers, params=params, timeout=10)
                    if retry_resp.status_code == 200:
                        return {"success": True, "data": retry_resp.json(), "refreshed": True}
                return {"success": False, "error": "카카오톡 API 오류: 401", "auth_required": True, "auth_url": build_kakao_authorize_url(), "provider": "kakao"}
            else:
                return {
                    "success": False,
                    "error": f"카카오톡 API 오류: {response.status_code}",
                    "error_message": response.text,
                    "status_code": response.status_code
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "카카오톡 API 호출 시간 초과"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"카카오톡 API 호출 실패: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}
    
    def send_message_to_friends(self, receiver_uuids, message, web_url=None, mobile_web_url=None, button_title=None):
        """
        카카오톡 친구에게 메시지 발송
        
        Args:
            receiver_uuids (list): 친구 UUID 리스트
            message (str): 발송할 메시지 내용 (최대 200자)
            web_url (str, optional): 웹 URL 링크
            mobile_web_url (str, optional): 모바일 웹 URL 링크
            button_title (str, optional): 버튼 제목
        
        Returns:
            dict: 발송 결과
        """
        if not self.access_token:
            return {
                "success": False,
                "error": "KAKAO_ACCESS_TOKEN이 설정되지 않았습니다."
            }
        
        if not receiver_uuids or not isinstance(receiver_uuids, list) or len(receiver_uuids) == 0:
            return {
                "success": False,
                "error": "receiver_uuids는 최소 1개 이상의 UUID 배열이어야 합니다."
            }
        
        # 메시지가 200자 초과 시 잘라내기
        if len(message) > 200:
            message = message[:197] + "..."
        
        # template_object 구성
        template_object = {
            "object_type": "text",
            "text": message,
            "link": {}
        }
        
        # 링크 정보 추가 (제공된 경우)
        if web_url:
            template_object["link"]["web_url"] = web_url
        if mobile_web_url:
            template_object["link"]["mobile_web_url"] = mobile_web_url
        
        # 버튼 제목 추가
        if button_title:
            template_object["button_title"] = button_title
        
        # API 엔드포인트
        friends_message_url = f"{os.getenv('KAKAO_API_BASE_URL', 'https://kapi.kakao.com')}/v1/api/talk/friends/message/default/send"
        
        # 헤더 설정
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Authorization': f'Bearer {self.access_token}'
        }
        
        # 데이터 준비
        data = {
            'receiver_uuids': json.dumps(receiver_uuids, ensure_ascii=False),
            'template_object': json.dumps(template_object, ensure_ascii=False)
        }
        
        try:
            print("[kakao_mcp_server] Messenger.send_message_to_friends -> endpoint", friends_message_url, "payload:", data)
            # 카카오톡 API 호출
            response = requests.post(
                friends_message_url,
                headers=headers,
                data=data,
                timeout=10
            )
            
            # 응답 확인
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "receiver_uuids": receiver_uuids,
                    "message": message,
                    "sent_at": datetime.now().isoformat(),
                    "successful_receiver_uuids": result.get("successful_receiver_uuids", []),
                    "failure_info": result.get("failure_info", []),
                    "api_response": result
                }
            elif response.status_code == 401:
                if self._attempt_refresh_and_update():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    retry_resp = requests.post(
                        friends_message_url,
                        headers=headers,
                        data=data,
                        timeout=10
                    )
                    if retry_resp.status_code == 200:
                        result = retry_resp.json()
                        return {
                            "success": True,
                            "receiver_uuids": receiver_uuids,
                            "message": message,
                            "sent_at": datetime.now().isoformat(),
                            "successful_receiver_uuids": result.get("successful_receiver_uuids", []),
                            "failure_info": result.get("failure_info", []),
                            "api_response": result,
                            "refreshed": True
                        }
                auth_url = build_kakao_authorize_url()
                return {
                    "success": False,
                    "error": "카카오톡 API 오류: 401",
                    "auth_required": True,
                    "auth_url": auth_url,
                    "provider": "kakao"
                }
            else:
                return {
                    "success": False,
                    "error": f"카카오톡 API 오류: {response.status_code}",
                    "error_message": response.text,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "카카오톡 API 호출 시간 초과"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"카카오톡 API 호출 실패: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"알 수 없는 오류: {str(e)}"
            }

# 전역 인스턴스
messenger = KakaoMessenger()

@app.route('/mcp/kakao/send', methods=['POST'])
def send_kakao_message():
    """
    MCP 엔드포인트: 카카오톡 메시지 발송
    
    Request Body:
    {
        "message": "안녕하세요",
        "web_url": "https://example.com",  // optional
        "mobile_web_url": "https://example.com",  // optional
        "button_title": "바로 확인"  // optional
    }
    """
    try:
        data = request.json
        print("[kakao_mcp_server] /mcp/kakao/send body:", data)
        
        if not data:
            return jsonify({"error": "Request body가 비어있습니다."}), 400
        
        message = data.get('message')
        web_url = data.get('web_url')
        mobile_web_url = data.get('mobile_web_url')
        button_title = data.get('button_title')
        template_id = data.get('template_id')
        
        if not message:
            return jsonify({
                "error": "message는 필수입니다."
            }), 400
        
        if template_id:
            template_args = data.get('template_args', {})
            # 템플릿 전송은 현재 receiver_id를 사용하지 않습니다
            print("[kakao_mcp_server] calling messenger.send_template_message (self memo path)")
            result = messenger.send_template_message(None, template_id, template_args)
        else:
            print("[kakao_mcp_server] calling messenger.send_message (self memo path)")
            result = messenger.send_message(
                message=message,
                web_url=web_url,
                mobile_web_url=mobile_web_url,
                button_title=button_title
            )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mcp/kakao/send-to-friends', methods=['POST'])
def send_kakao_message_to_friends():
    """
    MCP 엔드포인트: 카카오톡 친구에게 메시지 발송
    
    Request Body:
    {
        "receiver_uuids": ["uuid1", "uuid2", "uuid3"],  // required
        "message": "안녕하세요",
        "web_url": "https://example.com",  // optional
        "mobile_web_url": "https://example.com",  // optional
        "button_title": "바로 확인"  // optional
    }
    """
    try:
        data = request.json
        print("[kakao_mcp_server] /mcp/kakao/send-to-friends body:", data)
        
        if not data:
            return jsonify({"error": "Request body가 비어있습니다."}), 400
        
        receiver_uuids = data.get('receiver_uuids')
        message = data.get('message')
        web_url = data.get('web_url')
        mobile_web_url = data.get('mobile_web_url')
        button_title = data.get('button_title')
        
        if not receiver_uuids:
            return jsonify({
                "error": "receiver_uuids는 필수입니다."
            }), 400
        
        if not message:
            return jsonify({
                "error": "message는 필수입니다."
            }), 400
        
        print("[kakao_mcp_server] calling messenger.send_message_to_friends (friends path)")
        result = messenger.send_message_to_friends(
            receiver_uuids=receiver_uuids,
            message=message,
            web_url=web_url,
            mobile_web_url=mobile_web_url,
            button_title=button_title
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mcp/kakao/health', methods=['GET'])
def health_check():
    """MCP 서버 헬스 체크"""
    return jsonify({
        "status": "healthy",
        "service": "kakao_mcp_server",
        "version": "1.0.0"
    }), 200

@app.route('/mcp/kakao/capabilities', methods=['GET'])
def get_capabilities():
    """MCP 서버가 제공하는 기능 목록"""
    return jsonify({
        "tools": [
            {
                "name": "send_kakao_message",
                "description": "카카오톡 메시지 발송",
                "parameters": {
                    "message": "string (required) - 메시지 내용",
                    "template_id": "string (optional) - 템플릿 ID",
                    "web_url": "string (optional) - 웹 URL",
                    "mobile_web_url": "string (optional) - 모바일 웹 URL",
                    "button_title": "string (optional) - 버튼 제목"
                }
            },
            {
                "name": "get_kakao_friends",
                "description": "카카오톡 친구 목록 조회",
                "parameters": {
                    "offset": "number (optional) - 시작 위치",
                    "limit": "number (optional) - 조회 개수",
                    "order": "string (optional) - asc 또는 desc"
                }
            },
            {
                "name": "get_kakao_me",
                "description": "카카오 사용자 정보(내정보) 조회",
                "parameters": {}
            },
            {
                "name": "send_kakao_message_to_friends",
                "description": "카카오톡 친구에게 메시지 발송",
                "parameters": {
                    "receiver_uuids": "array (required) - 친구 UUID 배열",
                    "message": "string (required) - 메시지 내용",
                    "web_url": "string (optional) - 웹 URL",
                    "mobile_web_url": "string (optional) - 모바일 웹 URL",
                    "button_title": "string (optional) - 버튼 제목"
                }
            }
        ]
    }), 200

@app.route('/mcp/kakao/login', methods=['GET'])
def kakao_login():
    """카카오 OAuth 로그인: 브라우저 접근 시 Kakao auth로 리다이렉트, API는 JSON 제공"""
    if not KAKAO_REST_API_KEY:
        return jsonify({"success": False, "error": "KAKAO_REST_API_KEY 환경변수가 필요합니다."}), 500
    auth_url = build_kakao_authorize_url()

    # API 호출 등 JSON 선호 조건: format=json 쿼리 또는 Accept: application/json
    wants_json = (request.args.get('format') == 'json') or ('application/json' in (request.headers.get('Accept') or ''))
    if wants_json:
        return jsonify({"success": True, "auth_url": auth_url, "redirect_uri": KAKAO_REDIRECT_URI})

    # 브라우저 접근 기본: Kakao 인증 페이지로 리다이렉트
    return redirect(auth_url, code=302)

@app.route('/mcp/kakao/oauth/callback', methods=['GET'])
def kakao_oauth_callback():
    """카카오 OAuth 콜백: code로 토큰 교환 후 저장"""
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({"success": False, "error": "code 파라미터가 없습니다."}), 400
        token_response = exchange_code_for_tokens(code)
        existing = load_tokens()
        tokens_to_save = {
            'access_token': token_response.get('access_token'),
            'refresh_token': token_response.get('refresh_token') or existing.get('refresh_token'),
            'token_type': token_response.get('token_type'),
            'expires_in': token_response.get('expires_in'),
            'scope': token_response.get('scope'),
        }
        save_tokens(tokens_to_save)
        messenger._update_access_token_from_store()
        # 대화로 복귀 (웹채팅 UI)
        return redirect('http://127.0.0.1:5002/?kakao_auth=ok', code=302)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/kakao/token-status', methods=['GET'])
def kakao_token_status():
    tokens = load_tokens()
    masked = {
        'has_access_token': bool(tokens.get('access_token')),
        'has_refresh_token': bool(tokens.get('refresh_token')),
        'updated_at': tokens.get('updated_at')
    }
    return jsonify({"success": True, "tokens": masked, "redirect_uri": KAKAO_REDIRECT_URI}), 200

@app.route('/mcp/kakao/friends', methods=['GET'])
def get_kakao_friends():
    """MCP 엔드포인트: 카카오톡 친구 목록 조회"""
    try:
        offset = request.args.get('offset', default=None, type=int)
        limit = request.args.get('limit', default=None, type=int)
        order = request.args.get('order', default=None, type=str)

        result = messenger.get_friends(offset=offset, limit=limit, order=order)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/kakao/me', methods=['GET'])
def get_kakao_me():
    """MCP 엔드포인트: 카카오 사용자 정보(내정보) 조회"""
    try:
        result = messenger.get_my_info()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('MCP_SERVER_PORT', 5003))
    app.run(debug=True, host='0.0.0.0', port=port)

