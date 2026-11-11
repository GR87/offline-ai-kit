#!/bin/bash
# Downloads the Kiwix files listed in ~/zim-incoming/list.txt (.meta4 + .sha256 URLs, see
# kiwix-list.txt), checks every .zim against its .sha256, moves good files into ~/zim-files and
# rebuilds the library for http://localhost:8080. Safe to re-run: aria2 resumes, verified files
# already moved are skipped from the list.
set -uo pipefail
IN="$HOME/zim-incoming"
LIB="$HOME/zim-files"
LIST="$IN/list.txt"
TODO="$IN/todo.txt"

# Skip files that are already verified and in the library.
: > "$TODO"
while read -r url; do
  [ -z "$url" ] && continue
  name=$(basename "$url"); zim="${name%.meta4}"; zim="${zim%.sha256}"
  [ -f "$LIB/$zim" ] && [ -f "$LIB/$zim.sha256" ] && continue
  echo "$url" >> "$TODO"
done < "$LIST"
echo "$(date '+%d.%m.%y %H:%M') to fetch: $(grep -c '\.meta4$' "$TODO") files"

/opt/homebrew/bin/aria2c -i "$TODO" -d "$IN" -j 3 -c -V --follow-metalink=mem --file-allocation=none \
  --auto-file-renaming=false --max-tries=0 --retry-wait=30 --summary-interval=300 --console-log-level=warn

ok=0; bad=0
cd "$IN" || exit 1
for s in *.zim.sha256; do
  [ -f "$s" ] || continue
  z="${s%.sha256}"
  [ -f "$z" ] && [ ! -f "$z.aria2" ] || { echo "MISSING $z"; bad=$((bad+1)); continue; }
  if shasum -a 256 -c "$s" >/dev/null 2>&1; then mv "$z" "$s" "$LIB/" && ok=$((ok+1)) && echo "OK $z"
  else echo "FAILED $z"; bad=$((bad+1)); fi
done
"$LIB/refresh-library.sh"
echo "$(date '+%d.%m.%y %H:%M') done: $ok moved, $bad not ready"
