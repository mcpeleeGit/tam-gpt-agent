"""
GitHub 로컬 MCP 서버 (리포지토리 등 GitHub REST API 기능 래핑)

환경변수:
- GITHUB_TOKEN: GitHub Personal Access Token (classic or fine-grained)
- GITHUB_API_BASE: 기본 https://api.github.com
- GITHUB_MCP_PORT: 기본 5011
"""
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

# 프로젝트 루트의 .env 명시 로드
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=ENV_PATH)
app = Flask(__name__)

GITHUB_API_BASE = os.getenv('GITHUB_API_BASE', 'https://api.github.com')
GITHUB_DEFAULT_USER = os.getenv('GITHUB_DEFAULT_USER', '')

# GitHub 인증 헤더 생성 (로컬 MCP 서버 내부용)
def auth_headers():
    headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'tam-agent'
    }
    token = os.getenv('GITHUB_TOKEN', '')
    if token:
        prefix = 'Bearer'
        token_lower = token.lower()
        # GitHub 권장: classic 토큰(ghp_, gho_)은 'token', fine-grained 등은 'Bearer'
        if token_lower.startswith('ghp_') or token_lower.startswith('gho_'):
            prefix = 'token'
        headers['Authorization'] = f'{prefix} {token}'
    return headers

# 헬스 체크 엔드포인트 (MCP 서버 특화)
@app.route('/mcp/github/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "github_mcp_server"}), 200

@app.route('/mcp/github/token-status', methods=['GET'])
def token_status():
    token = os.getenv('GITHUB_TOKEN', '')
    kind = 'none'
    if token:
        tl = token.lower()
        if tl.startswith('ghp_') or tl.startswith('gho_'):
            kind = 'classic'
        else:
            kind = 'fine_grained_or_other'
    return jsonify({
        "has_token": bool(token),
        "token_kind": kind,
        "masked": f"{token[:4]}...{token[-4:]}" if token and len(token) >= 8 else None
    }), 200

# GitHub 리포지토리 목록 엔드포인트 (로컬 MCP 서버)
@app.route('/mcp/github/repos', methods=['GET'])
def list_repos():
    """사용자 리포지토리 목록 반환 (GitHub REST API 활용)

    Query params:
    - user: 특정 사용자 리포 (기본: 인증 사용자 me)
    - visibility: all|public|private (기본 all, 인증 필요 시 private 포함)
    - affiliation: owner,collaborator,organization_member 복합 지정 가능 (쉼표)
    - per_page: 기본 50
    - page: 기본 1
    """
    user = request.args.get('user')
    visibility = request.args.get('visibility', 'all')
    affiliation = request.args.get('affiliation')
    per_page = int(request.args.get('per_page', 50))
    page = int(request.args.get('page', 1))

    headers = auth_headers()

    if user:
        url = f"{GITHUB_API_BASE}/users/{user}/repos"
        params = {
            'per_page': per_page,
            'page': page,
            'type': 'all' if visibility == 'all' else visibility
        }
    else:
        # 인증 사용자 리포지토리
        url = f"{GITHUB_API_BASE}/user/repos"
        params = {
            'per_page': per_page,
            'page': page,
            'visibility': visibility
        }
        if affiliation:
            params['affiliation'] = affiliation

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            repos = r.json()
            simplified = [
                {
                    'id': repo.get('id'),
                    'name': repo.get('name'),
                    'full_name': repo.get('full_name'),
                    'private': repo.get('private'),
                    'html_url': repo.get('html_url'),
                    'description': repo.get('description'),
                    'language': repo.get('language'),
                    'archived': repo.get('archived'),
                    'pushed_at': repo.get('pushed_at'),
                    'visibility': repo.get('visibility') or ('private' if repo.get('private') else 'public')
                }
                for repo in repos
            ]
            return jsonify({"success": True, "repos": simplified, "count": len(simplified)}), 200
        else:
            # 401 처리: 토큰 문제이거나 미인증. 공개 조회인 경우 기본 사용자로 폴백 시도
            if r.status_code == 401 and not user and visibility == 'public' and GITHUB_DEFAULT_USER:
                fallback_url = f"{GITHUB_API_BASE}/users/{GITHUB_DEFAULT_USER}/repos"
                fb_params = {
                    'per_page': per_page,
                    'page': page,
                    'type': 'public'
                }
                fb = requests.get(fallback_url, params=fb_params, timeout=15)
                if fb.status_code == 200:
                    repos = fb.json()
                    simplified = [
                        {
                            'id': repo.get('id'),
                            'name': repo.get('name'),
                            'full_name': repo.get('full_name'),
                            'private': repo.get('private'),
                            'html_url': repo.get('html_url'),
                            'description': repo.get('description'),
                            'language': repo.get('language'),
                            'archived': repo.get('archived'),
                            'pushed_at': repo.get('pushed_at'),
                            'visibility': repo.get('visibility') or ('private' if repo.get('private') else 'public')
                        }
                        for repo in repos
                    ]
                    return jsonify({
                        "success": True,
                        "repos": simplified,
                        "count": len(simplified),
                        "note": f"no token/auth; fell back to GITHUB_DEFAULT_USER={GITHUB_DEFAULT_USER}"
                    }), 200
            return jsonify({
                "success": False,
                "status_code": r.status_code,
                "error": r.text
            }), r.status_code
    except requests.Timeout:
        return jsonify({"success": False, "error": "GitHub API 호출 시간 초과"}), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('GITHUB_MCP_PORT', 5011))
    app.run(debug=True, host='0.0.0.0', port=port)


