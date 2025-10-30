from data_manager import DataManager
from mcp_client import mcp_client
import json

# 전역 DataManager 인스턴스
data_manager = DataManager()

# OpenAI Function Calling을 위한 함수 정의들
FUNCTION_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_developer_status",
            "description": "데브톡 API로 개발자 계정 차단 여부 확인",
            "parameters": {
                "type": "object",
                "properties": {
                    "developer_id": {
                        "type": "string",
                        "description": "개발자 ID"
                    }
                },
                "required": ["developer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_info",
            "description": "고객 정보 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "고객 ID"
                    }
                },
                "required": ["customer_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_unblock_request",
            "description": "앱 차단 해제 요청 DB에 저장",
            "parameters": {
                "type": "object",
                "properties": {
                    "developer_id": {
                        "type": "string",
                        "description": "개발자 ID"
                    },
                    "reason": {
                        "type": "string",
                        "description": "차단 해제 요청 사유"
                    },
                    "additional_info": {
                        "type": "string",
                        "description": "추가 정보 (예: API 호출 로직 잘못으로 위반)"
                    }
                },
                "required": ["developer_id", "reason", "additional_info"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ticket_status",
            "description": "티켓 상태 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "티켓 ID"
                    }
                },
                "required": ["ticket_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "지원 티켓 생성",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "티켓 제목"
                    },
                    "description": {
                        "type": "string",
                        "description": "티켓 설명"
                    },
                    "priority": {
                        "type": "string",
                        "description": "우선순위 (low, medium, high, urgent)",
                        "enum": ["low", "medium", "high", "urgent"]
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "고객 ID (선택사항)"
                    }
                },
                "required": ["title", "description", "priority"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_app_error_logs",
            "description": "앱 ID로 에러 로그 조회 - KOE009 등 에러 코드 확인",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "앱 ID"
                    },
                    "error_code": {
                        "type": "string",
                        "description": "에러 코드 (예: KOE009)"
                    }
                },
                "required": ["app_id", "error_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_kakao_message",
            "description": "카카오톡 메시지 발송 - 자기 자신에게 메시지 보내기",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "발송할 메시지 내용 (필수)"
                    },
                    "template_id": {
                        "type": "string",
                        "description": "템플릿 ID (선택사항, 템플릿 메시지 사용 시)"
                    },
                    "web_url": {
                        "type": "string",
                        "description": "웹 URL 링크 (선택)"
                    },
                    "mobile_web_url": {
                        "type": "string",
                        "description": "모바일 웹 URL 링크 (선택)"
                    },
                    "button_title": {
                        "type": "string",
                        "description": "버튼 제목 (선택)"
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_famous_saying",
            "description": "랜덤 명언 조회 - 오늘의 명언, 명언 알려줘 등의 요청 시 사용",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kakao_friends",
            "description": "카카오톡 친구 목록 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "offset": {"type": "integer", "description": "시작 위치 (선택)"},
                    "limit": {"type": "integer", "description": "조회 개수 (선택)"},
                    "order": {"type": "string", "description": "정렬 (asc/desc) (선택)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kakao_me",
            "description": "카카오 사용자 정보(내정보) 조회",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_kakao_message_to_friends",
            "description": "카카오톡 친구에게 메시지 발송 - 친구 UUID 배열을 받아 여러 친구에게 메시지를 보냅니다",
            "parameters": {
                "type": "object",
                "properties": {
                    "receiver_uuids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "친구 UUID 배열 (필수, 최소 1개 이상)"
                    },
                    "message": {
                        "type": "string",
                        "description": "발송할 메시지 내용 (필수, 최대 200자)"
                    },
                    "web_url": {
                        "type": "string",
                        "description": "웹 URL 링크 (선택)"
                    },
                    "mobile_web_url": {
                        "type": "string",
                        "description": "모바일 웹 URL 링크 (선택)"
                    },
                    "button_title": {
                        "type": "string",
                        "description": "버튼 제목 (선택)"
                    }
                },
                "required": ["receiver_uuids", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tam_admin_action",
            "description": "tam-admin API 제너릭 액션 프록시(스펙 확정 전)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "수행할 액션명"},
                    "payload": {"type": "object", "description": "요청 바디(선택)"},
                    "method": {"type": "string", "description": "HTTP 메소드(기본 POST)"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_github_repos",
            "description": "GitHub 리포지토리 목록 조회 (인증 사용자 또는 특정 사용자)",
            "parameters": {
                "type": "object",
                "properties": {
                    "user": {"type": "string", "description": "특정 사용자명 (선택)"},
                    "visibility": {"type": "string", "description": "all|public|private (선택)"},
                    "affiliation": {"type": "string", "description": "owner,collaborator,organization_member (선택)"},
                    "per_page": {"type": "integer", "description": "페이지당 개수 (선택)"},
                    "page": {"type": "integer", "description": "페이지 번호 (선택)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_devtalk_unanswered_count",
            "description": "Devtalk 답변 없는 최근 작성글 수 조회",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_devtalk_unanswered_list",
            "description": "Devtalk 미답변 글 목록 조회",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "post_devtalk_reply",
            "description": "Devtalk 토픽에 답변 등록",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {"type": "integer", "description": "토픽 ID"},
                    "raw": {"type": "string", "description": "답변 본문"},
                    "target_recipients": {"type": "string", "description": "수신 대상 (선택)"},
                    "archetype": {"type": "string", "description": "유형 (선택)"}
                },
                "required": ["topic_id", "raw"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_devtalk_chat_matching_list",
            "description": "분류별 데브톡 사전 답변 목록 조회",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def execute_function(function_name, arguments):
    """함수 실행"""
    try:
        if function_name == "check_developer_status":
            developer_id = arguments.get("developer_id")
            developer = data_manager.get_developer_info(developer_id)
            if developer:
                result = {
                    "developer_id": developer.get("developer_id"),
                    "name": developer.get("name"),
                    "account_status": developer.get("account_status"),
                    "block_reason": developer.get("block_reason"),
                    "apps": developer.get("apps", []),
                    "notes": developer.get("notes")
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                return json.dumps({"error": "개발자 정보를 찾을 수 없습니다."}, ensure_ascii=False)
        
        elif function_name == "get_customer_info":
            customer_id = arguments.get("customer_id")
            customer = data_manager.get_customer(customer_id)
            if customer:
                result = {
                    "customer_id": customer.get("customer_id"),
                    "name": customer.get("name"),
                    "email": customer.get("email"),
                    "plan": customer.get("plan"),
                    "status": customer.get("status"),
                    "notes": customer.get("notes")
                }
                return json.dumps(result, ensure_ascii=False)
            else:
                return json.dumps({"error": "고객 정보를 찾을 수 없습니다."}, ensure_ascii=False)
        
        elif function_name == "create_unblock_request":
            developer_id = arguments.get("developer_id")
            reason = arguments.get("reason")
            additional_info = arguments.get("additional_info")
            
            request_data = {
                "developer_id": developer_id,
                "reason": reason,
                "additional_info": additional_info,
                "created_at": None,  # DataManager가 자동 생성
                "status": "pending"
            }
            
            result = data_manager.create_block_request(request_data)
            return json.dumps({
                "request_id": result.get("request_id"),
                "status": result.get("status"),
                "message": "차단 해제 요청이 등록되었습니다."
            }, ensure_ascii=False)
        
        elif function_name == "get_ticket_status":
            ticket_id = arguments.get("ticket_id")
            ticket = data_manager.get_ticket(ticket_id)
            if ticket:
                return json.dumps({
                    "ticket_id": ticket.get("ticket_id"),
                    "title": ticket.get("title"),
                    "status": ticket.get("status"),
                    "created_at": ticket.get("created_at"),
                    "description": ticket.get("description")
                }, ensure_ascii=False)
            else:
                return json.dumps({"error": "티켓을 찾을 수 없습니다."}, ensure_ascii=False)
        
        elif function_name == "create_ticket":
            ticket_data = {
                "title": arguments.get("title"),
                "description": arguments.get("description"),
                "priority": arguments.get("priority"),
                "customer_id": arguments.get("customer_id")
            }
            result = data_manager.create_ticket(ticket_data)
            return json.dumps({
                "ticket_id": result.get("ticket_id"),
                "title": result.get("title"),
                "status": result.get("status"),
                "message": "티켓이 생성되었습니다."
            }, ensure_ascii=False)
        
        elif function_name == "search_app_error_logs":
            app_id = arguments.get("app_id")
            error_code = arguments.get("error_code")
            
            # 실제로는 외부 로그 API를 호출해야 하지만, 여기서는 모의 데이터 사용
            # TODO: 실제 로그 API 연동 필요
            
            # 샘플 에러 로그 반환
            sample_logs = [
                {
                    "app_id": app_id,
                    "error_code": error_code,
                    "error_message": "웹 플랫폼 설정 오류: 관리자 설정이 올바르지 않습니다.",
                    "timestamp": "2024-10-26T10:30:00",
                    "severity": "error"
                }
            ]
            
            result = {
                "app_id": app_id,
                "error_code": error_code,
                "found": True,
                "logs": sample_logs,
                "total_count": len(sample_logs)
            }
            
            # DB에 티켓으로 저장 (일반적인 답변 티켓)
            ticket_data = {
                "title": f"앱 관리자 설정 오류 ({error_code})",
                "description": f"앱 ID: {app_id}, 에러 코드: {error_code}\n\n에러 메시지: {sample_logs[0]['error_message']}\n발생 시간: {sample_logs[0]['timestamp']}",
                "priority": "high",
                "customer_id": None
            }
            saved_ticket = data_manager.create_ticket(ticket_data)
            result["ticket_id"] = saved_ticket.get("ticket_id")
            
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "send_kakao_message":
            message = arguments.get("message")
            template_id = arguments.get("template_id")
            web_url = arguments.get("web_url")
            mobile_web_url = arguments.get("mobile_web_url")
            button_title = arguments.get("button_title")
            
            if not message:
                return json.dumps({"error": "message는 필수입니다."}, ensure_ascii=False)
            
            # 로그: 자기 자신(메모) 전송 경로
            print("[functions] Calling mcp_client.send_kakao_message", {
                "message": message,
                "template_id": template_id,
                "web_url": web_url,
                "mobile_web_url": mobile_web_url,
                "button_title": button_title
            })
            # MCP 서버를 통해 카카오톡 메시지 발송
            result = mcp_client.send_kakao_message(
                message=message,
                template_id=template_id,
                web_url=web_url,
                mobile_web_url=mobile_web_url,
                button_title=button_title
            )
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "get_famous_saying":
            # MCP 서버를 통해 랜덤 명언 조회
            result = mcp_client.get_famous_saying()
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "get_kakao_friends":
            offset = arguments.get("offset")
            limit = arguments.get("limit")
            order = arguments.get("order")
            result = mcp_client.get_kakao_friends(offset=offset, limit=limit, order=order)
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "get_kakao_me":
            result = mcp_client.get_kakao_me()
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "get_github_repos":
            user = arguments.get("user")
            visibility = arguments.get("visibility")
            affiliation = arguments.get("affiliation")
            per_page = arguments.get("per_page")
            page = arguments.get("page")
            result = mcp_client.get_github_repos(user=user, visibility=visibility, affiliation=affiliation, per_page=per_page, page=page)
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "send_kakao_message_to_friends":
            receiver_uuids = arguments.get("receiver_uuids")
            message = arguments.get("message")
            web_url = arguments.get("web_url")
            mobile_web_url = arguments.get("mobile_web_url")
            button_title = arguments.get("button_title")
            
            if not receiver_uuids or not isinstance(receiver_uuids, list) or len(receiver_uuids) == 0:
                return json.dumps({"error": "receiver_uuids는 최소 1개 이상의 UUID 배열이어야 합니다."}, ensure_ascii=False)
            
            if not message:
                return json.dumps({"error": "message는 필수입니다."}, ensure_ascii=False)
            
            # 로그: 친구 전송 경로
            print("[functions] Calling mcp_client.send_kakao_message_to_friends", {
                "receiver_uuids": receiver_uuids,
                "message": message,
                "web_url": web_url,
                "mobile_web_url": mobile_web_url,
                "button_title": button_title
            })
            # MCP 서버를 통해 친구들에게 카카오톡 메시지 발송
            result = mcp_client.send_kakao_message_to_friends(
                receiver_uuids=receiver_uuids,
                message=message,
                web_url=web_url,
                mobile_web_url=mobile_web_url,
                button_title=button_title
            )
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "tam_admin_action":
            action = arguments.get("action")
            payload = arguments.get("payload")
            method = arguments.get("method") or "POST"
            result = mcp_client.tam_admin_proxy(action=action, payload=payload, method=method)
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "get_devtalk_unanswered_count":
            result = mcp_client.get_devtalk_unanswered_count()
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "get_devtalk_unanswered_list":
            result = mcp_client.get_devtalk_unanswered_list()
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "post_devtalk_reply":
            topic_id = arguments.get("topic_id")
            raw = arguments.get("raw")
            target_recipients = arguments.get("target_recipients")
            archetype = arguments.get("archetype")
            if not topic_id or not raw:
                return json.dumps({"error": "topic_id와 raw는 필수입니다."}, ensure_ascii=False)
            result = mcp_client.post_devtalk_reply(topic_id=topic_id, raw=raw, target_recipients=target_recipients, archetype=archetype)
            return json.dumps(result, ensure_ascii=False)
        
        elif function_name == "get_devtalk_chat_matching_list":
            result = mcp_client.get_devtalk_chat_matching_list()
            return json.dumps(result, ensure_ascii=False)
        
        else:
            return json.dumps({"error": f"알 수 없는 함수: {function_name}"}, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

