"""
Devtalk MCP 서버 - 답변 없는 최근 작성글 수 조회
"""
from flask import Flask, jsonify, request
import os
import requests
from dotenv import load_dotenv

# .env 로드 (프로젝트 루트 기준)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)

DEVTALK_HOST = os.getenv('DEVTALK_HOST', 'https://devtalk.kakao.com')
DEVTALK_API_KEY = os.getenv('DEVTALK_API_KEY', '')
DEVTALK_API_USERNAME = os.getenv('DEVTALK_API_USERNAME', '')
DEVTALK_REPLY_API_KEY = os.getenv('DEVTALK_REPLY_API_KEY', '')
DEVTALK_REPLY_API_USERNAME = os.getenv('DEVTALK_REPLY_API_USERNAME', '')

@app.route('/mcp/devtalk/health', methods=['GET'])
def health():
	return jsonify({"status": "healthy", "service": "devtalk_mcp_server", "version": "1.0.0"}), 200

@app.route('/mcp/devtalk/capabilities', methods=['GET'])
def capabilities():
	return jsonify({
		"tools": [
			{
				"name": "get_devtalk_unanswered_count",
				"description": "Devtalk 답변 없는 최근 작성글 수 조회",
				"parameters": {}
			},
			{
				"name": "post_devtalk_reply",
				"description": "Devtalk 토픽에 답변 등록",
				"parameters": {
					"topic_id": "number (required)",
					"raw": "string (required) - 답변 본문",
					"target_recipients": "string (optional) - 기본 tambot",
					"archetype": "string (optional) - 기본 regular"
				}
			},
			{
				"name": "get_devtalk_unanswered_list",
				"description": "Devtalk 미답변 글 목록 조회",
				"parameters": {}
			}
		]
	}), 200

@app.route('/mcp/devtalk/unanswered-count', methods=['GET'])
def get_unanswered_count():
	"""Devtalk Explorer Query(13) 실행 - 답변 없는 최근 작성글 수"""
	if not DEVTALK_API_KEY or not DEVTALK_API_USERNAME:
		return jsonify({"success": False, "error": "DEVTALK_API_KEY/DEVTALK_API_USERNAME가 설정되지 않았습니다."}), 400
	url = f"{DEVTALK_HOST}/admin/plugins/explorer/queries/13/run"
	headers = {
		'Api-Key': DEVTALK_API_KEY,
		'Api-Username': DEVTALK_API_USERNAME
	}
	try:
		# multipart/form-data는 requests가 boundary를 설정하도록 files 또는 data 사용
		# 본문이 필요 없다면 빈 data로 전달
		resp = requests.post(url, headers=headers, data={}, timeout=10)
		if resp.status_code == 200:
			# Explorer 결과 포맷 그대로 전달
			return jsonify({"success": True, "data": resp.json()}), 200
		else:
			return jsonify({
				"success": False,
				"error": f"Devtalk API 오류: {resp.status_code}",
				"error_message": resp.text,
				"status_code": resp.status_code
			}), resp.status_code
	except requests.exceptions.Timeout:
		return jsonify({"success": False, "error": "Devtalk API 호출 시간 초과"}), 504
	except requests.exceptions.RequestException as e:
		return jsonify({"success": False, "error": f"Devtalk API 호출 실패: {str(e)}"}), 502
	except Exception as e:
		return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/devtalk/unanswered-list', methods=['GET'])
def get_unanswered_list():
    """Devtalk Explorer Query(12) 실행 - 미답변 글 목록 조회"""
    if not DEVTALK_API_KEY or not DEVTALK_API_USERNAME:
        return jsonify({"success": False, "error": "DEVTALK_API_KEY/DEVTALK_API_USERNAME가 설정되지 않았습니다."}), 400
    url = f"{DEVTALK_HOST}/admin/plugins/explorer/queries/12/run"
    headers = {
        'Api-Key': DEVTALK_API_KEY,
        'Api-Username': DEVTALK_API_USERNAME
    }
    try:
        resp = requests.post(url, headers=headers, data={}, timeout=10)
        if resp.status_code == 200:
            return jsonify({"success": True, "data": resp.json()}), 200
        else:
            return jsonify({
                "success": False,
                "error": f"Devtalk API 오류: {resp.status_code}",
                "error_message": resp.text,
                "status_code": resp.status_code
            }), resp.status_code
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "Devtalk API 호출 시간 초과"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Devtalk API 호출 실패: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/mcp/devtalk/reply', methods=['POST'])
def post_reply():
	"""Devtalk 토픽에 답변 등록"""
	if not DEVTALK_REPLY_API_KEY or not DEVTALK_REPLY_API_USERNAME:
		return jsonify({"success": False, "error": "DEVTALK_REPLY_API_KEY/DEVTALK_REPLY_API_USERNAME가 설정되지 않았습니다."}), 400
	try:
		body = request.get_json(silent=True) or {}
		topic_id = body.get('topic_id')
		raw = body.get('raw')
		target_recipients = body.get('target_recipients') or 'tambot'
		archetype = body.get('archetype') or 'regular'

		if not topic_id or not raw:
			return jsonify({"success": False, "error": "topic_id와 raw는 필수입니다."}), 400

		url = f"{DEVTALK_HOST}/posts.json"
		headers = {
			'Content-Type': 'application/json;charset=utf-8',
			'Api-Key': DEVTALK_REPLY_API_KEY,
			'Api-Username': DEVTALK_REPLY_API_USERNAME
		}
		payload = {
			'raw': raw,
			'topic_id': str(topic_id),
			'target_recipients': target_recipients,
			'archetype': archetype
		}

		resp = requests.post(url, headers=headers, json=payload, timeout=15)
		if resp.status_code in (200, 201):
			return jsonify({"success": True, "data": resp.json()}), 200
		else:
			return jsonify({
				"success": False,
				"error": f"Devtalk API 오류: {resp.status_code}",
				"error_message": resp.text,
				"status_code": resp.status_code
			}), resp.status_code
	except requests.exceptions.Timeout:
		return jsonify({"success": False, "error": "Devtalk API 호출 시간 초과"}), 504
	except requests.exceptions.RequestException as e:
		return jsonify({"success": False, "error": f"Devtalk API 호출 실패: {str(e)}"}), 502
	except Exception as e:
		return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
	port = int(os.getenv('DEVTALK_MCP_SERVER_PORT', 5006))
	app.run(debug=True, host='0.0.0.0', port=port)
