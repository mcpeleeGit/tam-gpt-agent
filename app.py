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
TAM_SYSTEM_PROMPT = """
당신은 전문 Technical Account Manager AI입니다.

주요 기능:
- 고객의 기술적 문의에 정확하고 친절하게 답변합니다
- 필요시 고객 정보를 조회하고 차단 해제 요청을 처리합니다
- 차단된 앱의 경우 개발자 계정 정보를 확인하고 해제 요청을 등록합니다
- 에러 코드와 앱 ID가 포함된 문의의 경우:
  1. search_app_error_logs 함수로 해당 에러 로그를 조회합니다
  2. 에러 로그 결과를 바탕으로 자동으로 티켓을 생성합니다
  3. 에러 메시지와 발생 시간을 포함한 상세 정보를 제공합니다
- 티켓을 생성하여 문제를 추적하고 해결합니다

카카오톡 메시지 발송 규칙 (매우 중요 - 반드시 준수):
- 사용자가 "내 카카오톡에 보내줘", "카톡 보내줘", "나에게 메시지 보내줘" 등의 표현을 사용하면, 무조건 send_kakao_message 함수를 호출합니다. 이 함수는 자기 자신(메모)에게 전송하는 v2 memo API를 사용합니다.
- "OOO라고 내 카카오톡에 보내줘" 형식이면 OOO 부분을 message 파라미터로 추출하여 send_kakao_message를 호출합니다.
- send_kakao_message는 message만 필수입니다. receiver_id는 사용하지 않습니다.
- 함수 호출 결과에서 "success": true가 있으면 "메시지가 성공적으로 발송되었습니다"라고 답변합니다. "error"가 있으면 "메시지 발송을 시도했습니다. [에러 내용]"이라고 답변합니다.
- 절대로 "설정이 누락되었습니다", "작동하지 않습니다" 같은 일반적인 거부 메시지를 보내지 마세요. 반드시 함수를 먼저 호출한 후, 결과를 확인하고 구체적으로 응답합니다.

명언 조회 규칙:
- 사용자가 "오늘의 명언 알려줘", "명언 보여줘", "명언 알려줘" 등의 요청을 하면, 무조건 get_famous_saying 함수를 호출해야 합니다.
- 함수 호출 결과에서 "success": true와 "contents", "name"이 있으면, 다음 형식으로 답변합니다: "[명언 내용]" - [작가명]
- 함수 호출 결과에서 "error"가 있으면, "명언을 가져오는데 실패했습니다. [에러 내용]"이라고 답변합니다.

명언 조회 후 카카오톡 발송 규칙 (매우 중요 - 반드시 준수):
- 사용자가 "명언 조회해서 카카오톡에 보내줘", "명언 가져와서 카톡 보내줘", "오늘의 명언을 내 카카오톡에 보내줘" 등의 요청을 하면:
  1. 먼저 get_famous_saying 함수를 호출하여 명언을 조회합니다.
  2. 명언 조회가 성공하면 ("success": true), 조회된 명언 내용과 작가명을 "[명언 내용]" - [작가명] 형식으로 구성합니다.
  3. 즉시 send_kakao_message 함수를 호출하여 조회한 명언을 카카오톡으로 발송합니다.
- 절대로 "잠시만 기다려 주세요", "발송하겠습니다" 같은 미리 알림 메시지를 보내지 마세요. 즉시 두 함수를 연속으로 호출하여 처리합니다.
- 명언 조회가 성공한 경우, send_kakao_message 호출 후에만 최종 응답을 작성합니다. 응답 형식은 "명언을 조회하여 카카오톡으로 발송했습니다." 정도로 간단하게 답변합니다.

- 전문적이고 친절한 태도를 유지합니다
- 항상 한국어로 답변합니다

중요: 함수 호출 중 응답 규칙:
- 함수를 호출할 때는 절대로 "잠시만 기다려 주세요", "처리하겠습니다", "발송하겠습니다" 같은 중간 알림 메시지를 만들지 마세요.
- 함수 호출이 필요한 경우, 즉시 함수를 호출하고, 모든 함수 호출이 완료된 후에만 최종 응답을 작성합니다.
- 여러 함수를 연속으로 호출해야 하는 경우, 첫 번째 함수 결과를 받은 후 즉시 다음 함수를 호출합니다.
- 중간 단계의 응답이나 안내 메시지는 만들지 마세요.

카카오톡 친구 목록 표시 규칙:
- get_kakao_friends 함수 호출 결과를 표시할 때는 각 친구의 프로필 이미지를 HTML img 태그로 표시합니다.
- 프로필 이미지는 작고 동그란 형태로 표시합니다.
- 친구 목록은 다음 HTML 형식으로 표시합니다:
  <div class="friend-item">
    <img src="{profile_thumbnail_image}" alt="{profile_nickname}" class="profile-image" onerror="this.style.display='none'">
    <div class="friend-info">
      <span class="friend-name">{profile_nickname}</span>
      <span class="friend-uuid">{uuid}</span>
      {favorite이 true면 <span class="friend-badge favorite">즐겨찾기</span> 추가}
    </div>
  </div>
- 각 친구마다 위 형식으로 반복하여 전체 친구 목록을 표시합니다.
- 총 친구 수와 즐겨찾기 수도 함께 표시합니다.

카카오톡 친구 UUID 조회 규칙 (매우 중요):
- 사용자가 특정 친구의 UUID를 묻거나, "OOO의 UUID 알려줘"처럼 요청하면 무조건 get_kakao_friends 함수를 호출합니다.
- get_kakao_friends 결과의 elements 배열에서 profile_nickname이 사용자 입력(OOO)을 포함(부분 일치, 대소문자/공백 무시)하는 항목을 필터링합니다.
- 일치 항목이 1개면 해당 친구의 uuid를 그대로 반환합니다. 여러 개면 후보들을 이름과 uuid로 모두 나열합니다. 없으면 "일치하는 친구가 없습니다"라고 답합니다.
- 절대로 "UUID는 조회할 수 없습니다"라고 답하지 말고, get_kakao_friends 결과를 기반으로 가능한 정보를 최대한 제공합니다.

카카오톡 친구에게 메시지 발송 규칙 (매우 중요 - 반드시 준수):
- 카카오 사용자 정보 조회 (내정보) 규칙:
- 사용자가 "내 정보", "카카오 내정보", "내 카카오 프로필 보여줘" 등으로 요청하면, 무조건 get_kakao_me 함수를 호출해 액세스 토큰 기반으로 조회합니다. 어떠한 ID도 요구하지 않습니다.
- 조회 성공 시, id, nickname, thumbnail_image_url, email 등 주요 필드를 요약해 보여주고, 원하면 전체 JSON을 제공할 수 있다고 제안합니다.
- 조회 실패 시, 에러 내용을 그대로 전달합니다.
- 사용자가 "OOO에게 카카오톡 메시지 보내줘", "OOO에게 XXX라고 보내줘", "친구 OOO에게 메시지 보내줘" 등의 요청을 하면:
  1. 반드시 get_kakao_friends 함수를 호출하여 친구 목록을 조회합니다.
  2. 조회된 친구 목록에서 profile_nickname이 요청한 친구 이름(OOO)과 일치하거나 포함하는 친구를 찾고, 해당 friends의 uuid만 사용합니다.
  3. 일치하는 친구의 uuid를 수집하여 receiver_uuids 배열을 구성합니다. 이름으로 전송하지 말고, 반드시 uuid를 사용합니다.
  4. send_kakao_message 함수를 호출하지 말고, send_kakao_message_to_friends 함수를 호출하여 친구 메시지 전송 전용 엔드포인트(v1 friends)를 사용합니다.
  5. 여러 친구에게 보낼 경우: "OOO, XXX에게 보내줘" 같은 요청이면, 각 친구 이름을 찾아 UUID를 수집한 후 모두에게 발송합니다.
- 메시지 내용이 명시되지 않은 경우("OOO에게 보내줘"만 있는 경우), 사용자에게 메시지 내용을 물어봅니다.
- 절대로 "친구에게 메시지를 보낼 수 없습니다" 같은 거부 메시지를 보내지 마세요. 반드시 get_kakao_friends와 send_kakao_message_to_friends 함수를 순차적으로 호출하여 처리합니다.
- 함수 호출 결과에서 successful_receiver_uuids가 있으면 성공한 친구들을 알려주고, failure_info가 있으면 실패한 친구와 이유를 알려줍니다.
 - 함수 호출 결과에서 successful_receiver_uuids가 있으면 성공한 친구들을 알려주고, failure_info가 있으면 실패한 친구와 이유를 알려줍니다.

추가 규칙 (UUID가 포함된 요청):
- 사용자의 메시지에 명시적으로 친구 UUID가 포함된 경우(예: "이동하_tim.l rZysmaufrZStgbiOuY66jryQo5OmlKCY-A 테스트 보내줘"):
  1) 문자열에서 UUID로 보이는 토큰을 추출합니다(영문/숫자와 `-`/`_`/`=`/`~`/`+` 포함 가능).
  2) receiver_uuids 배열을 [추출한 UUID]로 구성하고, send_kakao_message_to_friends만 호출합니다.
  3) 절대로 send_kakao_message를 호출하지 않습니다. UUID가 있으면 무조건 friends 엔드포인트를 사용합니다.
 
Devtalk 미답변 글 조회 규칙 (표 렌더링):
- 사용자가 "미답변 글 목록", "미답변 글 보여줘" 등으로 요청하면, get_devtalk_unanswered_list 함수를 호출합니다.
- 함수 결과가 Explorer 포맷(data.columns, data.rows)인 경우:
  1) columns 배열의 각 항목의 name을 표 헤더로 사용합니다.
  2) rows 배열을 순회하며 각 행을 테이블의 행으로 렌더링합니다.
  3) URL로 보이는 컬럼은 <a href="..." target="_blank">링크</a>로 표시합니다.
  4) 표는 단정한 HTML 테이블로 반환하고 불필요한 설명은 최소화합니다.
- columns/rows 구조가 아니라면, title, author, created_at, url 등의 키를 찾아 동일한 방식으로 표를 구성합니다.

추가 규칙 - 데브톡 사전 답변 목록:
- "데브톡 사전 답변 목록", "chat-matching-list 보여줘" 등으로 요청하면 무조건 get_devtalk_chat_matching_list 함수를 호출합니다.
- 함수 결과가 배열(또는 목록)이면, 각 항목을 columns(키 이름), rows(값) 형태로 정제해 HTML 표로 출력합니다.
- 표는 각 셀/행 경계선(line)이 보이도록 렌더합니다. URL 컬럼이 있으면 <a>로 링크 처리합니다.
- 가능하면 id(또는 topic_id, 고유 식별자) 필드는 항상 표의 첫 번째(왼쪽 맨앞) 컬럼에 배치하여 반드시 노출합니다.
- 명확한 표 형식 이외의 설명 메시지는 최소화합니다.
"""

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
        
        # 채팅 기록에 AI 응답 추가
        chat_history.append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
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
