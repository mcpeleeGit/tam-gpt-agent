"""
랜덤 명언 조회 MCP 서버
Model Context Protocol을 통해 GPT 에이전트가 오늘의 명언을 조회할 수 있도록 지원
"""
from flask import Flask, request, jsonify
import os
import requests
from datetime import datetime

app = Flask(__name__)

# 명언 API 설정
FAMOUSSAYING_API_URL = os.getenv('FAMOUSSAYING_API_URL', 'http://test-tam.pe.kr/api/famoussaying')

class FamousSayingClient:
    """랜덤 명언 조회 클래스"""
    
    def __init__(self, api_url=None):
        self.api_url = api_url or FAMOUSSAYING_API_URL
    
    def get_random_famous_saying(self):
        """
        랜덤 명언 조회
        
        Returns:
            dict: 명언 정보 {"contents": "명언 내용", "name": "작가명"}
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "contents": result.get("contents", ""),
                "name": result.get("name", ""),
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "명언 API 호출 시간 초과"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"명언 API 호출 실패: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"알 수 없는 오류: {str(e)}"
            }

# 전역 인스턴스
famous_saying_client = FamousSayingClient()

@app.route('/mcp/famoussaying/get', methods=['GET'])
def get_famous_saying():
    """
    MCP 엔드포인트: 랜덤 명언 조회
    
    Response:
    {
        "success": true,
        "contents": "명언 내용",
        "name": "작가명",
        "fetched_at": "2024-10-29T23:00:00"
    }
    """
    try:
        result = famous_saying_client.get_random_famous_saying()
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/famoussaying/health', methods=['GET'])
def health_check():
    """MCP 서버 헬스 체크"""
    return jsonify({
        "status": "healthy",
        "service": "famoussaying_mcp_server",
        "version": "1.0.0"
    }), 200

@app.route('/mcp/famoussaying/capabilities', methods=['GET'])
def get_capabilities():
    """MCP 서버가 제공하는 기능 목록"""
    return jsonify({
        "tools": [
            {
                "name": "get_famous_saying",
                "description": "랜덤 명언 조회",
                "method": "GET"
            }
        ]
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('FAMOUSSAYING_MCP_SERVER_PORT', 5004))
    app.run(debug=True, host='0.0.0.0', port=port)

