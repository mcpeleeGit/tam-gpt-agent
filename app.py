from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
from datetime import datetime
from dotenv import load_dotenv
import json
from functions import FUNCTION_DEFINITIONS, execute_function

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)

# OpenAI API 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 채팅 기록을 저장할 리스트
chat_history = []

# TAM System Prompt
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts/system_prompt.txt")
with open(PROMPT_PATH, encoding="utf-8") as f:
    TAM_SYSTEM_PROMPT = f.read()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        
        if not user_message:
            return jsonify({'error': '메시지가 비어있습니다.'}), 400
        
        # 채팅 기록에 사용자 메시지 추가
        chat_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        # OpenAI API 호출 - 채팅 기록을 API 형식으로 변환
        api_messages = [
            {"role": "system", "content": TAM_SYSTEM_PROMPT}
        ]
        
        # 채팅 기록에서 role과 content만 추출
        for msg in chat_history[-10:]:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Function Calling이 포함된 응답
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=api_messages,
            tools=FUNCTION_DEFINITIONS,
            tool_choice="auto",
            max_tokens=2000
        )
        
        message = response.choices[0].message
        
        # 디버깅: 함수 호출 여부 확인
        print(f"=== GPT Response ===")
        print(f"Content: {message.content}")
        print(f"Tool calls: {message.tool_calls}")
        
        # Function 호출이 있으면 여러 라운드로 처리 (최대 5라운드)
        # 첫 응답의 content는 무시 (함수 호출 중에는 중간 메시지를 만들지 않도록)
        ai_response = ""
        max_rounds = 5
        round_count = 0
        
        while message.tool_calls and round_count < max_rounds:
            round_count += 1
            print(f"=== Function Calling Round {round_count} ===")
            
            # 함수 호출 메시지를 추가 (첫 라운드부터)
            api_messages.append(message)
            
            # 각 function 호출 처리
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # 디버깅 로그
                print(f"=== Function Call ===")
                print(f"Function: {function_name}")
                print(f"Arguments: {arguments}")
                
                # 함수 실행
                function_result = execute_function(function_name, arguments)
                
                print(f"Result: {function_result}")
                
                # 결과를 메시지에 추가
                api_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_result
                })
            
            # 함수 실행 결과를 바탕으로 다음 응답 생성 (다음 라운드의 함수 호출 또는 최종 응답)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                tools=FUNCTION_DEFINITIONS,
                tool_choice="auto",
                max_tokens=2000
            )
            message = response.choices[0].message
            
            # 더 이상 함수 호출이 없으면 최종 응답 저장하고 종료
            if not message.tool_calls:
                ai_response = message.content or ""
                break
        
        # 함수 호출이 없었던 경우 (처음부터 응답만 있었던 경우)
        if not message.tool_calls and ai_response == "":
            ai_response = message.content or ""
        
        # Kakao 인증 필요 신호를 탐지해 로그인 버튼 노출을 위한 구조화 응답으로 변환
        response_payload = None
        try:
            # 간단한 휴리스틱: 인증 관련 키워드 탐지
            lower_text = (ai_response or '').lower()
            if ('401' in lower_text and 'kakao' in lower_text) or ('인증' in ai_response and '카카오' in ai_response) or ('로그인' in ai_response and '카카오' in ai_response):
                kakao_login_url = f"http://127.0.0.1:{int(os.getenv('MCP_SERVER_PORT', 5003))}/mcp/kakao/login"
                response_payload = {
                    'auth_required': True,
                    'auth_url': kakao_login_url
                }
        except Exception:
            pass

        # 채팅 기록에 AI 응답 추가 (표시용 텍스트는 그대로 저장)
        chat_history.append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

        # 클라이언트로는 auth_required 신호가 있으면 구조화 응답을, 아니면 순수 텍스트를 반환
        if response_payload is not None:
            return jsonify({
                'response': response_payload,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        else:
            return jsonify({
                'response': ai_response,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        
    except Exception as e:
        return jsonify({'error': f'오류가 발생했습니다: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    global chat_history
    chat_history = []
    return jsonify({'message': '채팅 기록이 삭제되었습니다.'})

@app.route('/history')
def get_history():
    return jsonify({'history': chat_history})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
