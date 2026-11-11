#!/bin/bash
# Rebuilds the Kiwix library from every .zim in ~/zim-files, so the local site at
# http://localhost:8080 shows new files. Run after adding or removing a .zim.
set -euo pipefail
DIR="$HOME/zim-files"
BIN="$HOME/Applications/kiwix-tools"
LIB="$DIR/library.xml"
rm -f "$LIB.tmp"
for z in "$DIR"/*.zim; do "$BIN/kiwix-manage" "$LIB.tmp" add "$z"; done
mv "$LIB.tmp" "$LIB"
echo "library: $(grep -c '<book ' "$LIB") files"
