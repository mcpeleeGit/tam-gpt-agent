"""
MCP 서버 호출 클라이언트
"""
import requests
import json
import os

class MCPClient:
    """MCP 서버와 통신하는 클라이언트"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('MCP_SERVER_URL', 'http://localhost:5003')
    
    def send_kakao_message(self, receiver_id, message, template_id=None):
        """
        카카오톡 메시지 발송 (MCP 서버 호출)
        
        Args:
            receiver_id (str): 수신자 ID
            message (str): 메시지 내용
            template_id (str, optional): 템플릿 ID
        
        Returns:
            dict: 발송 결과
        """
        try:
            url = f"{self.base_url}/mcp/kakao/send"
            payload = {
                "receiver_id": receiver_id,
                "message": message
            }
            
            if template_id:
                payload["template_id"] = template_id
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"MCP 서버 호출 오류: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"알 수 없는 오류: {str(e)}"
            }
    
    def health_check(self):
        """MCP 서버 헬스 체크"""
        try:
            url = f"{self.base_url}/mcp/kakao/health"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_famous_saying(self, base_url=None):
        """
        랜덤 명언 조회 (명언 MCP 서버 호출)
        
        Args:
            base_url (str, optional): 명언 MCP 서버 URL (기본값: http://localhost:5004)
        
        Returns:
            dict: 명언 정보
        """
        try:
            famoussaying_url = base_url or os.getenv('FAMOUSSAYING_MCP_SERVER_URL', 'http://localhost:5004')
            url = f"{famoussaying_url}/mcp/famoussaying/get"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"명언 MCP 서버 호출 오류: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"알 수 없는 오류: {str(e)}"
            }

    def get_kakao_friends(self, offset=None, limit=None, order=None):
        """카카오 MCP 서버를 통해 친구 목록 조회"""
        try:
            params = {}
            if offset is not None:
                params['offset'] = offset
            if limit is not None:
                params['limit'] = limit
            if order is not None:
                params['order'] = order

            url = f"{self.base_url}/mcp/kakao/friends"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"MCP 서버 호출 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}
    
    def send_kakao_message_to_friends(self, receiver_uuids, message, web_url=None, mobile_web_url=None, button_title=None):
        """
        카카오톡 친구에게 메시지 발송 (MCP 서버 호출)
        
        Args:
            receiver_uuids (list): 친구 UUID 리스트
            message (str): 메시지 내용
            web_url (str, optional): 웹 URL
            mobile_web_url (str, optional): 모바일 웹 URL
            button_title (str, optional): 버튼 제목
        
        Returns:
            dict: 발송 결과
        """
        try:
            url = f"{self.base_url}/mcp/kakao/send-to-friends"
            payload = {
                "receiver_uuids": receiver_uuids,
                "message": message
            }
            
            if web_url:
                payload["web_url"] = web_url
            if mobile_web_url:
                payload["mobile_web_url"] = mobile_web_url
            if button_title:
                payload["button_title"] = button_title
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"MCP 서버 호출 오류: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"알 수 없는 오류: {str(e)}"
            }

# 전역 인스턴스
mcp_client = MCPClient()

