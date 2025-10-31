#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/donghalee/Cursor/flask/agent"
TMP_DIR="$ROOT_DIR/tmp"
LOG_DIR="$ROOT_DIR/tmp"
PY="python3"

mkdir -p "$TMP_DIR"

# service(name, cmd, port, pidfile, logfile)
service() {
  local name="$1"; shift
  local cmd="$1"; shift
  local port="$1"; shift
  local pidfile="$1"; shift
  local logfile="$1"; shift
  echo "$name|$cmd|$port|$pidfile|$logfile"
}

SERVICES=(
  "$(service webchat   "$PY $ROOT_DIR/app.py"                                               5002 "$TMP_DIR/app5002.pid"        "$LOG_DIR/webchat.log")"
  "$(service kakao     "$PY $ROOT_DIR/mcp_server/kakao_mcp_server.py"                      5003 "$TMP_DIR/kakao5003.pid"       "$LOG_DIR/kakao_mcp.log")"
  "$(service famous    "$PY $ROOT_DIR/mcp_server/famoussaying_mcp_server.py"               5004 "$TMP_DIR/famous5004.pid"      "$LOG_DIR/famoussaying_mcp.log")"
  "$(service tamadmin  "$PY $ROOT_DIR/mcp_server/tam_admin_mcp_server.py"                   5005 "$TMP_DIR/tamadmin5005.pid"    "$LOG_DIR/tam_admin_mcp.log")"
  "$(service devtalk   "$PY $ROOT_DIR/mcp_server/devtalk_mcp_server.py"                    5006 "$TMP_DIR/devtalk5006.pid"     "$LOG_DIR/devtalk_mcp.log")"
  "$(service github    "$PY $ROOT_DIR/mcp_server/github_mcp_server.py"                     5011 "$TMP_DIR/github5011.pid"      "$LOG_DIR/github_mcp.log")"
  "$(service kcalendar "$PY $ROOT_DIR/mcp_server/kakao_calendar_mcp_server.py"             5012 "$TMP_DIR/kcalendar5012.pid"   "$LOG_DIR/kakao_calendar_mcp.log")"
)

color() { local c="$1"; shift; printf "\033[%sm%s\033[0m\n" "$c" "$*"; }
green() { color 32 "$@"; }
yellow() { color 33 "$@"; }
red() { color 31 "$@"; }

is_running_pid() { local pid="$1"; [[ -n "$pid" && -d "/proc/$pid" ]] 2>/dev/null || kill -0 "$pid" 2>/dev/null; }

find_pid_on_port() { lsof -ti :"$1" 2>/dev/null || true; }

start_one() {
  local entry="$1"
  IFS='|' read -r name cmd port pidfile logfile <<<"$entry"
  if [[ -f "$pidfile" ]]; then
    local pid; pid=$(cat "$pidfile" 2>/dev/null || true)
    if is_running_pid "$pid"; then
      yellow "[skip] $name already running (pid=$pid, port=$port)"
      return 0
    fi
  fi
  # If port busy, try kill existing
  local pids; pids=$(find_pid_on_port "$port")
  if [[ -n "$pids" ]]; then
    yellow "[info] freeing port $port for $name (pids: $pids)"
    echo "$pids" | xargs -I{} kill -9 {} 2>/dev/null || true
    sleep 0.5
  fi
  nohup bash -lc "$cmd" >>"$logfile" 2>&1 &
  local npid=$!
  echo "$npid" > "$pidfile"
  green "[up] $name started (pid=$npid, port=$port, log=$(basename "$logfile"))"
}

stop_one() {
  local entry="$1"
  IFS='|' read -r name cmd port pidfile logfile <<<"$entry"
  local stopped=false
  if [[ -f "$pidfile" ]]; then
    local pid; pid=$(cat "$pidfile" 2>/dev/null || true)
    if is_running_pid "$pid"; then
      kill "$pid" 2>/dev/null || true
      sleep 0.5
      if is_running_pid "$pid"; then kill -9 "$pid" 2>/dev/null || true; fi
      stopped=true
    fi
    rm -f "$pidfile" 2>/dev/null || true
  fi
  local pids; pids=$(find_pid_on_port "$port")
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs -I{} kill -9 {} 2>/dev/null || true
    stopped=true
  fi
  if $stopped; then green "[down] $name stopped"; else yellow "[skip] $name not running"; fi
}

status_one() {
  local entry="$1"
  IFS='|' read -r name cmd port pidfile logfile <<<"$entry"
  local pids; pids=$(find_pid_on_port "$port")
  if [[ -n "$pids" ]]; then
    echo "$(printf '%-10s' "$name") : running (port=$port pid=$pids) log=$(basename "$logfile")"
  else
    echo "$(printf '%-10s' "$name") : stopped (port=$port)"
  fi
}

start_all() { for s in "${SERVICES[@]}"; do start_one "$s"; done; }
stop_all()  { for s in "${SERVICES[@]}"; do stop_one  "$s"; done; }
status_all(){ for s in "${SERVICES[@]}"; do status_one "$s"; done; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [start|stop|restart|status]

Services:
  - webchat  (port 5002)
  - kakao    (port 5003)
  - famous   (port 5004)
  - tamadmin (port 5005)
  - devtalk  (port 5006)
  - github   (port 5011)
  - kcalendar(port 5012)

Logs: $LOG_DIR/*.log
PIDs: $TMP_DIR/*.pid
EOF
}

cmd="${1:-}"
case "$cmd" in
  start)   start_all ;;
  stop)    stop_all  ;;
  restart) stop_all; start_all ;;
  status)  status_all;;
  *) usage; exit 1;;
esac


