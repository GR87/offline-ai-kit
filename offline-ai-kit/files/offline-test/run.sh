#!/bin/bash
# Offline test: model server + questions + library search, all inside a sandbox that blocks the internet.
# Usage: run.sh <output-folder>   (re-run continues where it stopped)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:?output folder}"; mkdir -p "$OUT"
SB="$HERE/offline.sb"
MODEL="${MODEL:?set MODEL=<path to the .gguf file>}"
PY="$HOME/.local/share/uv/tools/openzim-mcp/bin/python"

{
  echo "== $(date '+%d.%m.%y %H:%M:%S') network check inside the sandbox"
  for u in https://www.google.com https://1.1.1.1 https://lmstudio.ai; do
    if code=$(sandbox-exec -f "$SB" /usr/bin/curl -s -m 8 -o /dev/null -w "%{http_code}" "$u"); then echo "$u -> HTTP $code"
    else echo "$u -> blocked (curl exit $?)"; fi
  done
  sandbox-exec -f "$SB" /usr/bin/curl -s -m 8 -o /dev/null -w "http://127.0.0.1:8080 (local Wikipedia) -> HTTP %{http_code}\n" http://127.0.0.1:8080/
} > "$OUT/network-check.txt"

~/.lmstudio/bin/lms unload --all >/dev/null 2>&1
sandbox-exec -f "$SB" /opt/homebrew/bin/llama-server -m "$MODEL" --jinja -c "${CTX:-32768}" -ngl 99 \
  --reasoning-format none --host 127.0.0.1 --port 8090 --no-webui > "$OUT/llama-server.log" 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
until curl -s -m 2 http://127.0.0.1:8090/health | grep -q ok; do sleep 2; kill -0 $SRV || exit 1; done

sandbox-exec -f "$SB" "$PY" -I "$HERE/run.py" "${QFILE:-$HERE/questions.json}" "$OUT" &
RUN=$!
# While the questions run, record every network connection the three processes hold (expect localhost only).
while kill -0 $RUN 2>/dev/null; do
  { date '+%H:%M:%S'; lsof -nP -i -a -p "$SRV,$RUN,$(pgrep -d, -P $RUN)" 2>/dev/null | awk 'NR>1{print $1, $8, $9, $10}'; } >> "$OUT/connections.log"
  sleep 20
done
wait $RUN
