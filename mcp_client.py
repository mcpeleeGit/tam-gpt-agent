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
        # tam-admin MCP 서버 URL (별도 포트/서비스)
        self.tam_admin_base_url = os.getenv('TAM_ADMIN_MCP_SERVER_URL', 'http://localhost:5005')
        # devtalk MCP 서버 URL
        self.devtalk_base_url = os.getenv('DEVTALK_MCP_SERVER_URL', 'http://localhost:5006')
        # github MCP 서버 URL
        self.github_base_url = os.getenv('GITHUB_MCP_SERVER_URL', 'http://localhost:5011')
    
    def send_kakao_message(self, message, template_id=None, web_url=None, mobile_web_url=None, button_title=None):
        """
        카카오톡 메시지 발송 (MCP 서버 호출)
        
        Args:
            message (str): 메시지 내용
            template_id (str, optional): 템플릿 ID
            web_url (str, optional): 웹 URL
            mobile_web_url (str, optional): 모바일 웹 URL
            button_title (str, optional): 버튼 제목
        
        Returns:
            dict: 발송 결과
        """
        try:
            url = f"{self.base_url}/mcp/kakao/send"
            payload = {
                "message": message
            }
            
            if template_id:
                payload["template_id"] = template_id
            if web_url:
                payload["web_url"] = web_url
            if mobile_web_url:
                payload["mobile_web_url"] = mobile_web_url
            if button_title:
                payload["button_title"] = button_title
            
            print("[mcp_client] POST /mcp/kakao/send", {"url": url, "payload": payload})
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
    
    def get_kakao_me(self):
        """카카오 MCP 서버를 통해 사용자 정보(내정보) 조회"""
        try:
            url = f"{self.base_url}/mcp/kakao/me"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"MCP 서버 호출 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}

    # ===== github MCP 연동 =====
    def get_github_repos(self, user=None, visibility=None, affiliation=None, per_page=None, page=None):
        try:
            url = f"{self.github_base_url}/mcp/github/repos"
            params = {}
            if user:
                params['user'] = user
            if visibility:
                params['visibility'] = visibility
            if affiliation:
                params['affiliation'] = affiliation
            if per_page:
                params['per_page'] = per_page
            if page:
                params['page'] = page
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"GitHub MCP 서버 호출 오류: {str(e)}"}
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
            
            print("[mcp_client] POST /mcp/kakao/send-to-friends", {"url": url, "payload": payload})
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

    # ===== tam-admin MCP 연동 =====
    def tam_admin_health(self):
        """tam-admin MCP 서버 헬스 체크"""
        try:
            url = f"{self.tam_admin_base_url}/mcp/tam-admin/health"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def tam_admin_capabilities(self):
        """tam-admin MCP 서버 capabilities 조회"""
        try:
            url = f"{self.tam_admin_base_url}/mcp/tam-admin/capabilities"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def tam_admin_proxy(self, action, payload=None, method='POST'):
        """
        tam-admin MCP 제너릭 프록시 호출

        Args:
            action (str): 수행할 액션명
            payload (dict|None): 요청 바디
            method (str): HTTP 메소드 (기본 POST)
        Returns:
            dict
        """
        try:
            url = f"{self.tam_admin_base_url}/mcp/tam-admin/proxy"
            body = {"action": action, "payload": payload or {}, "method": method}
            response = requests.post(url, json=body, timeout=10)
            # 501도 JSON 본문을 담고 있으므로 raise_for_status를 쓰지 않고 그대로 반환 처리
            try:
                return response.json()
            except ValueError:
                return {"error": "Invalid JSON from tam-admin MCP", "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"tam-admin MCP 서버 호출 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}

    # ===== devtalk MCP 연동 =====
    def devtalk_health(self):
        try:
            url = f"{self.devtalk_base_url}/mcp/devtalk/health"
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def get_devtalk_unanswered_count(self):
        try:
            url = f"{self.devtalk_base_url}/mcp/devtalk/unanswered-count"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Devtalk MCP 서버 호출 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}

    def get_devtalk_unanswered_list(self):
        try:
            url = f"{self.devtalk_base_url}/mcp/devtalk/unanswered-list"
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Devtalk MCP 서버 호출 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}

    def post_devtalk_reply(self, topic_id, raw, target_recipients=None, archetype=None):
        try:
            url = f"{self.devtalk_base_url}/mcp/devtalk/reply"
            payload = {"topic_id": topic_id, "raw": raw}
            if target_recipients:
                payload["target_recipients"] = target_recipients
            if archetype:
                payload["archetype"] = archetype
            r = requests.post(url, json=payload, timeout=15)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Devtalk MCP 서버 호출 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}

    def get_devtalk_chat_matching_list(self):
        """분류별 데브톡 사전 답변 목록 조회 (tam-admin MCP)"""
        try:
            tamadmin_url = os.getenv('TAM_ADMIN_MCP_SERVER_URL', 'http://localhost:5005')
            url = tamadmin_url.rstrip('/') + '/mcp/tam-admin/devtalk-chat-matching-list'
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            return {"success": False, "error": f"tam-admin MCP 서버 호출 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"알 수 없는 오류: {str(e)}"}

# 전역 인스턴스
mcp_client = MCPClient()

