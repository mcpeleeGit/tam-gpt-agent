"""
tam-admin API 연동을 위한 로컬 MCP 서버 (스캐폴딩)

현재는 헬스체크 및 기능 목록(capabilities)만 제공하고,
제너릭 프록시 엔드포인트는 501(Not Implemented)을 반환합니다.

환경 변수:
- TAM_ADMIN_API_BASE_URL: 실제 tam-admin API 루트 URL (미정)
- TAM_ADMIN_MCP_SERVER_PORT: 이 MCP 서버 포트 (기본 5005)
"""
import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드 (mcp_server 디렉토리에서 실행될 수 있으므로 상위 디렉토리 지정)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

# 환경 설정
TAM_ADMIN_API_BASE_URL = os.getenv('TAM_ADMIN_API_BASE_URL', '')
TAM_ADMIN_API_HOST = os.getenv('TAM_ADMIN_API_HOST', '')
TAM_ADMIN_API_AUTH = 'Basic'
TAM_ADMIN_API_UA = 'tam-batch'
TAM_ADMIN_CLIENT = 'TAM-AGENT'

@app.route('/mcp/tam-admin/health', methods=['GET'])
def health_check():
    """MCP 서버 헬스 체크"""
    return jsonify({
        "status": "healthy",
        "service": "tam_admin_mcp_server",
        "version": "1.0.0",
        "tam_admin_api_base": bool(TAM_ADMIN_API_BASE_URL)
    }), 200

@app.route('/mcp/tam-admin/capabilities', methods=['GET'])
def get_capabilities():
    """MCP 서버가 제공(예정)하는 기능 목록(placeholder)"""
    return jsonify({
        "tools": [
            {
                "name": "tam_admin_action",
                "description": "tam-admin API에 대한 제너릭 액션 프록시 (스펙 확정 전)",
                "parameters": {
                    "action": "string (required) - 수행할 액션명",
                    "payload": "object (optional) - 요청 바디",
                    "method": "string (optional) - HTTP 메소드 (기본 POST)"
                }
            },
            {
                "name": "get_devtalk_chat_matching_list",
                "description": "분류별 데브톡 사전 답변 목록 조회",
                "parameters": {}
            }
        ]
    }), 200

@app.route('/mcp/tam-admin/devtalk-chat-matching-list', methods=['GET'])
def devtalk_chat_matching_list():
    """
    분류별 데브톡 사전 답변 목록 조회 프록시 - page=1, limit=20 기본값 적용
    """
    if not TAM_ADMIN_API_HOST:
        return jsonify({"success": False, "error": "TAM_ADMIN_API_HOST env not set"}), 500

    url = TAM_ADMIN_API_HOST.rstrip("/") + "/api/devtalk/chat-matching-list"
    params = {}
    for k in ('major_category', 'sub_category', 'page', 'limit'):
        v = request.args.get(k)
        if v is not None:
            params[k] = v
    # 기본값 적용
    if 'page' not in params:
        params['page'] = 1
    if 'limit' not in params:
        params['limit'] = 20
    headers = {
        "Authorization": TAM_ADMIN_API_AUTH,
        "User-Agent": TAM_ADMIN_API_UA,
        "TAM-CLIENT": TAM_ADMIN_CLIENT,
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return jsonify({"success": True, "data": resp.json()}), 200
        else:
            return jsonify({
                "success": False,
                "error": f"tam-admin API 오류: {resp.status_code}",
                "error_message": resp.text,
                "status_code": resp.status_code,
            }), resp.status_code
    except requests.Timeout:
        return jsonify({"success": False, "error": "tam-admin API 호출 시간 초과"}), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/tam-admin/proxy', methods=['POST'])
def tam_admin_proxy():
    """
    제너릭 프록시 (스펙 확정 전): 현재는 501 반환

    Request Body 예시:
    {
        "action": "get_customer",
        "payload": { ... },
        "method": "POST"
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        action = data.get('action')
        payload = data.get('payload')
        method = data.get('method', 'POST').upper()

        return jsonify({
            "success": False,
            "error": "Not Implemented",
            "message": "tam-admin API 스펙 확정 전입니다.",
            "action": action,
            "method": method,
            "timestamp": datetime.now().isoformat()
        }), 501
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('TAM_ADMIN_MCP_SERVER_PORT', 5005))
    app.run(debug=True, host='0.0.0.0', port=port)


