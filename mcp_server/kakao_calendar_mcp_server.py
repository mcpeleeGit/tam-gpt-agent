"""
카카오 캘린더 로컬 MCP 서버

제공 기능:
- POST /mcp/kakao-calendar/create/calendar  (사용자 서브 캘린더 생성)
- POST /mcp/kakao-calendar/create/event     (사용자 일정 생성)
- GET  /mcp/kakao-calendar/holidays         (공휴일/기념일 조회 - Admin Key 사용)
- GET  /mcp/kakao-calendar/health
- GET  /mcp/kakao-calendar/capabilities

환경변수:
- KAKAO_API_BASE_URL (기본 https://kapi.kakao.com)
- KAKAO_ACCESS_TOKEN (사용자 API용 Bearer 액세스 토큰)
- KAKAO_ADMIN_KEY    (공휴일 API용 KakaoAK {ADMIN_KEY})
- KAKAO_CAL_MCP_PORT (기본 5012)
"""
import os
import json
from flask import Flask, request, jsonify
import requests
from datetime import datetime
from dotenv import load_dotenv

# .env 로드 (프로젝트 루트)
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=ENV_PATH)

app = Flask(__name__)

KAKAO_API_BASE_URL = os.getenv('KAKAO_API_BASE_URL', 'https://kapi.kakao.com')
KAKAO_ACCESS_TOKEN = os.getenv('KAKAO_ACCESS_TOKEN', '')
KAKAO_ADMIN_KEY = os.getenv('KAKAO_ADMIN_KEY', '')

# kakao_mcp_server와 동일한 토큰 저장소 사용
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

def bearer_headers():
    tokens = load_tokens()
    token = tokens.get('access_token') or os.getenv('KAKAO_ACCESS_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
    }

def admin_headers():
    admin = os.getenv('KAKAO_ADMIN_KEY', '')
    return {
        'Authorization': f'KakaoAK {admin}'
    }

@app.route('/mcp/kakao-calendar/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "kakao_calendar_mcp_server", "version": "1.0.0"}), 200

@app.route('/mcp/kakao-calendar/capabilities', methods=['GET'])
def capabilities():
    return jsonify({
        "tools": [
            {"name": "create_kakao_calendar", "description": "사용자 서브 캘린더 생성", "parameters": {"name": "string", "color": "string", "reminder": "number", "reminder_all_day": "number"}},
            {"name": "create_kakao_calendar_event", "description": "사용자 일정 생성", "parameters": {"calendar_id": "string", "event": "object(JSON)"}},
            {"name": "get_kakao_calendar_holidays", "description": "공휴일/기념일 조회", "parameters": {"from": "ISO8601", "to": "ISO8601"}}
        ]
    }), 200

@app.route('/mcp/kakao-calendar/create/calendar', methods=['POST'])
def create_calendar():
    try:
        data = request.get_json(silent=True) or {}
        name = data.get('name') or '서비스 캘린더'
        color = data.get('color') or 'RED'
        reminder = data.get('reminder')
        reminder_all_day = data.get('reminder_all_day')

        form = { 'name': name, 'color': color }
        if reminder is not None: form['reminder'] = str(reminder)
        if reminder_all_day is not None: form['reminder_all_day'] = str(reminder_all_day)

        url = f"{KAKAO_API_BASE_URL}/v2/api/calendar/create/calendar"
        res = requests.post(url, headers=bearer_headers(), data=form, timeout=10)
        if res.status_code == 200:
            return jsonify({"success": True, **res.json()}), 200
        elif res.status_code == 401:
            # 상세 에러 로깅
            try:
                print("[kakao_calendar_mcp] create_calendar 401 body:", res.text)
            except Exception:
                pass
            return jsonify({"success": False, "error": "카카오톡 API 오류: 401", "auth_required": True, "provider": "kakao", "error_body": res.text}), 401
        # 기타 에러 로깅
        try:
            print("[kakao_calendar_mcp] create_calendar error:", res.status_code, res.text)
        except Exception:
            pass
        return jsonify({"success": False, "status_code": res.status_code, "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/kakao-calendar/create/event', methods=['POST'])
def create_event():
    try:
        data = request.get_json(silent=True) or {}
        calendar_id = data.get('calendar_id')
        event = data.get('event')
        if not calendar_id or not event:
            return jsonify({"success": False, "error": "calendar_id와 event는 필수입니다."}), 400

        # event는 JSON 문자열로 전달해야 함
        # 보정: 키 오타 및 필드 기본값 처리
        try:
            if isinstance(event, dict):
                # 'rrlue' 오타 자동 수정 -> 'rrule'
                if 'rrlue' in event and 'rrule' not in event:
                    event['rrule'] = event.pop('rrlue')
                # time 기본값/보정
                t = event.get('time') or {}
                if isinstance(t, dict):
                    # 기본 타임존 설정
                    if not t.get('time_zone'):
                        t['time_zone'] = 'Asia/Seoul'
                    # all_day/lunar 기본값
                    if 'all_day' not in t:
                        t['all_day'] = False
                    if 'lunar' not in t:
                        t['lunar'] = False
                    # end_at이 없으면 start_at + 1시간
                    if t.get('start_at') and not t.get('end_at'):
                        try:
                            from datetime import datetime, timedelta, timezone
                            # ISO8601 Z 또는 오프셋 허용
                            sa = t['start_at']
                            # datetime.fromisoformat supports '+09:00' but not 'Z' -> handle Z
                            if sa.endswith('Z'):
                                dt = datetime.fromisoformat(sa.replace('Z', '+00:00'))
                            else:
                                dt = datetime.fromisoformat(sa)
                            dt_end = dt + timedelta(hours=1)
                            # 출력은 Z(UTC) 표기 사용
                            t['end_at'] = dt_end.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
                        except Exception:
                            # 실패시 end_at은 그대로 생략
                            pass
                    event['time'] = t
        except Exception:
            pass

        form = {
            'calendar_id': calendar_id,
            'event': json.dumps(event, ensure_ascii=False)
        }
        url = f"{KAKAO_API_BASE_URL}/v2/api/calendar/create/event"
        res = requests.post(url, headers=bearer_headers(), data=form, timeout=10)
        if res.status_code == 200:
            return jsonify({"success": True, **res.json()}), 200
        elif res.status_code == 401:
            try:
                print("[kakao_calendar_mcp] create_event 401 body:", res.text)
            except Exception:
                pass
            return jsonify({"success": False, "error": "카카오톡 API 오류: 401", "auth_required": True, "provider": "kakao", "error_body": res.text}), 401
        try:
            print("[kakao_calendar_mcp] create_event error:", res.status_code, res.text)
        except Exception:
            pass
        return jsonify({"success": False, "status_code": res.status_code, "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/kakao-calendar/create/event-simple', methods=['POST'])
def create_event_simple():
    """간단 일정 생성: calendar_id, title, start_local(YYYY-MM-DD HH:MM), duration_minutes(기본 60)

    예시 body:
    {
      "calendar_id": "user_xxx",
      "title": "회의",
      "start_local": "2025-11-05 12:00",
      "duration_minutes": 60,
      "description": "메모",
      "color": "RED"
    }
    """
    try:
        body = request.get_json(silent=True) or {}
        calendar_id = body.get('calendar_id')
        title = body.get('title')
        start_local = body.get('start_local')  # Asia/Seoul 기준
        duration_minutes = int(body.get('duration_minutes') or 60)
        description = body.get('description')
        color = body.get('color')
        if not calendar_id or not title or not start_local:
            return jsonify({"success": False, "error": "calendar_id, title, start_local은 필수입니다."}), 400

        from datetime import datetime, timedelta, timezone
        try:
            # 우선 완전한 형식 시도
            dt_local = datetime.strptime(start_local, '%Y-%m-%d %H:%M')
        except ValueError:
            # 연도 생략 형식 보정: 기본 연도는 올해로
            try:
                from datetime import date
                this_year = date.today().year
                # 지원: MM-DD HH:MM, M-D HH:MM, MM/DD HH:MM
                try:
                    dt_partial = datetime.strptime(start_local, '%m-%d %H:%M')
                except ValueError:
                    dt_partial = datetime.strptime(start_local, '%m/%d %H:%M')
                dt_local = dt_partial.replace(year=this_year)
            except Exception:
                return jsonify({"success": False, "error": "start_local 형식은 YYYY-MM-DD HH:MM 또는 MM-DD HH:MM 이어야 합니다."}), 400
        KST = timezone(timedelta(hours=9))
        dt_local_kst = dt_local.replace(tzinfo=KST)
        dt_utc_start = dt_local_kst.astimezone(timezone.utc)
        dt_utc_end = dt_utc_start + timedelta(minutes=duration_minutes)

        event = {
            "title": title,
            "time": {
                "start_at": dt_utc_start.isoformat().replace('+00:00', 'Z'),
                "end_at": dt_utc_end.isoformat().replace('+00:00', 'Z'),
                "time_zone": "Asia/Seoul",
                "all_day": False,
                "lunar": False
            }
        }
        if description:
            event["description"] = description
        if color:
            event["color"] = color

        form = {
            'calendar_id': calendar_id,
            'event': json.dumps(event, ensure_ascii=False)
        }
        url = f"{KAKAO_API_BASE_URL}/v2/api/calendar/create/event"
        res = requests.post(url, headers=bearer_headers(), data=form, timeout=10)
        if res.status_code == 200:
            return jsonify({"success": True, **res.json(), "normalized_event": event}), 200
        elif res.status_code == 401:
            try:
                print("[kakao_calendar_mcp] create_event_simple 401 body:", res.text)
            except Exception:
                pass
            return jsonify({"success": False, "error": "카카오톡 API 오류: 401", "auth_required": True, "provider": "kakao", "error_body": res.text}), 401
        try:
            print("[kakao_calendar_mcp] create_event_simple error:", res.status_code, res.text)
        except Exception:
            pass
        return jsonify({"success": False, "status_code": res.status_code, "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/kakao-calendar/holidays', methods=['GET'])
def get_holidays():
    try:
        q_from = request.args.get('from')
        q_to = request.args.get('to')
        if not q_from or not q_to:
            return jsonify({"success": False, "error": "from, to 파라미터는 필수입니다."}), 400
        params = { 'from': q_from, 'to': q_to }
        url = f"{KAKAO_API_BASE_URL}/v2/api/calendar/holidays"
        res = requests.get(url, headers=admin_headers(), params=params, timeout=10)
        if res.status_code == 200:
            return jsonify({"success": True, **res.json()}), 200
        try:
            print("[kakao_calendar_mcp] holidays error:", res.status_code, res.text)
        except Exception:
            pass
        return jsonify({"success": False, "status_code": res.status_code, "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/kakao-calendar/calendars', methods=['GET'])
def list_calendars():
    """사용자 캘린더/구독 캘린더 목록 조회

    Query:
      - filter: USER | SUBSCRIBE | ALL (기본 ALL)
    """
    try:
        flt = request.args.get('filter')  # USER, SUBSCRIBE, ALL
        params = {}
        if flt:
            params['filter'] = flt
        url = f"{KAKAO_API_BASE_URL}/v2/api/calendar/calendars"
        res = requests.get(url, headers=bearer_headers(), params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return jsonify({"success": True, **data}), 200
        elif res.status_code == 401:
            try:
                print("[kakao_calendar_mcp] calendars 401 body:", res.text)
            except Exception:
                pass
            return jsonify({"success": False, "error": "카카오톡 API 오류: 401", "auth_required": True, "provider": "kakao", "error_body": res.text}), 401
        try:
            print("[kakao_calendar_mcp] calendars error:", res.status_code, res.text)
        except Exception:
            pass
        return jsonify({"success": False, "status_code": res.status_code, "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/kakao-calendar/events', methods=['GET'])
def list_events():
    """일정 목록 조회

    Query:
      - calendar_id: 필수
      - from: ISO8601 (UTC, e.g., 2025-11-01T00:00:00Z)
      - to:   ISO8601 (UTC)
      - limit: 숫자(선택)
    """
    try:
        calendar_id = request.args.get('calendar_id')
        q_from = request.args.get('from')
        q_to = request.args.get('to')
        q_limit = request.args.get('limit')
        if not calendar_id:
            return jsonify({"success": False, "error": "calendar_id는 필수입니다."}), 400
        params = { 'calendar_id': calendar_id }
        # 기본 기간: 현재 달 1일 00:00 KST ~ 다음 달 1일 00:00 KST (UTC Z로 변환)
        if not q_from or not q_to:
            try:
                from datetime import datetime, timedelta, timezone
                KST = timezone(timedelta(hours=9))
                now_kst = datetime.now(KST)
                first_day = now_kst.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                # 다음 달 1일 계산
                if first_day.month == 12:
                    next_month_first = first_day.replace(year=first_day.year+1, month=1)
                else:
                    next_month_first = first_day.replace(month=first_day.month+1)
                from_utc = first_day.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
                to_utc = next_month_first.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
                if not q_from:
                    q_from = from_utc
                if not q_to:
                    q_to = to_utc
            except Exception:
                pass
        if q_from: params['from'] = q_from
        if q_to: params['to'] = q_to
        if q_limit: params['limit'] = q_limit
        url = f"{KAKAO_API_BASE_URL}/v2/api/calendar/events"
        res = requests.get(url, headers=bearer_headers(), params=params, timeout=12)
        if res.status_code == 200:
            return jsonify({"success": True, **res.json()}), 200
        elif res.status_code == 401:
            try:
                print("[kakao_calendar_mcp] events 401 body:", res.text)
            except Exception:
                pass
            return jsonify({"success": False, "error": "카카오톡 API 오류: 401", "auth_required": True, "provider": "kakao", "error_body": res.text}), 401
        try:
            print("[kakao_calendar_mcp] events error:", res.status_code, res.text)
        except Exception:
            pass
        return jsonify({"success": False, "status_code": res.status_code, "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('KAKAO_CAL_MCP_PORT', 5012))
    app.run(debug=True, host='0.0.0.0', port=port)


