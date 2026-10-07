#!/usr/bin/env bash
# Génère le site et le publie : sources sur main, site sur gh-pages.
set -euo pipefail
cd "$(dirname "$0")"
pip install -q markdown --break-system-packages 2>/dev/null || pip install -q markdown
python3 build.py
NAME="Yann Collin"; MAIL="yanncollin23@users.noreply.github.com"
git add -A
git -c user.name="$NAME" -c user.email="$MAIL" commit -qm "${1:-Mise à jour du site}" || true
git push -q origin main
TMP="$(mktemp -d)"
cp -r docs/. "$TMP"
cd "$TMP"
git init -q -b gh-pages
git add -A
git -c user.name="$NAME" -c user.email="$MAIL" commit -qm "Publication du site"
git push -qf "$(git -C "$OLDPWD" remote get-url origin)" gh-pages
echo "Site publié."
