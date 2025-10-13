#!/usr/bin/env bash
set -euo pipefail

FRONT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$FRONT_DIR/server"

# Load .env so both processes see API_URL, API_PORT, FRONT_PORT, etc.
set -a
[ -f "$FRONT_DIR/.env" ] && . "$FRONT_DIR/.env"
set +a

# Show listeners on a TCP port and ask before killing them
prompt_kill_port() {
    local port="$1"
    echo "Checking listeners on TCP port ${port}..."

    local have_lsof have_fuser
    command -v lsof >/dev/null 2>&1 && have_lsof=1 || have_lsof=0
    command -v fuser >/dev/null 2>&1 && have_fuser=1 || have_fuser=0

    local pids=""
    if [ "$have_lsof" -eq 1 ]; then
        local listing
        listing="$(lsof -nP -iTCP:${port} -sTCP:LISTEN 2>/dev/null || true)"
        if [ -n "$listing" ]; then
            echo "$listing"
            pids="$(lsof -t -nP -iTCP:${port} -sTCP:LISTEN 2>/dev/null || true)"
        fi
    elif [ "$have_fuser" -eq 1 ]; then
        pids="$(fuser -n tcp "${port}" 2>/dev/null || true)"
        if [ -n "$pids" ]; then
            echo "PID(s) listening on ${port}: ${pids}"
            for pid in $pids; do
                ps -o pid=,user=,comm=,args= -p "$pid" || true
            done
        fi
    else
        echo "No lsof/fuser available to inspect port ${port}."
        return 0
    fi

    if [ -z "$pids" ]; then
        echo "No listener on port ${port}"
        return 0
    fi

    read -r -p "Kill these process(es) on port ${port}? [y/N] " reply
    case "$reply" in
        [yY]|[yY][eE][sS])
            echo "Terminating PID(s): $pids"
            kill -TERM $pids 2>/dev/null || true
            sleep 0.5
            for pid in $pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    echo "Force killing PID $pid"
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            done
            ;;
        *)
            echo "Skipping kill on port ${port}"
            ;;
    esac
}

# Install dependencies
cd "$FRONT_DIR"
npm i --no-audit --no-fund

cd "$SERVER_DIR"
npm i --no-audit --no-fund

# Run both; stop on exit
trap 'jobs -p | xargs -r kill' EXIT

# Ask to free dev ports if occupied
prompt_kill_port 5173
prompt_kill_port 5174

( cd "$FRONT_DIR" && npm run dev ) &
( cd "$SERVER_DIR" && npm start ) &

wait