#!/bin/bash
# Réinstalle les skills de Yann dans ~/.claude/skills si la session a été recréée.
# Source : le zip claude-skills-main (MIT, alirezarezvani) + les 2 skills Collective Brain.
set -e
T=~/.claude/skills; mkdir -p "$T"
[ "$(ls "$T" | wc -l)" -ge 400 ] && { echo "skills déjà installés ($(ls "$T" | wc -l))"; exit 0; }
Z=$(ls /mnt/user-data/outputs/claude-skills-main.zip /mnt/user-data/attachments/*/*claude-skills-main.zip 2>/dev/null | head -1)
[ -z "$Z" ] && { echo "zip claude-skills-main introuvable : le redemander à Yann"; exit 1; }
W=$(mktemp -d); unzip -q "$Z" -d "$W"
python3 - "$W" "$T" <<'P'
import os,re,shutil,sys
src,T=sys.argv[1],sys.argv[2];seen=set();n=0
for root,dirs,files in os.walk(src):
    if "SKILL.md" in files:
        m=re.search(r"^name:\s*['\"]?([A-Za-z0-9._-]+)",open(os.path.join(root,"SKILL.md"),encoding="utf-8",errors="ignore").read(),re.M)
        if not m or m.group(1) in seen: continue
        seen.add(m.group(1)); d=os.path.join(T,m.group(1))
        if not os.path.exists(d): shutil.copytree(root,d,ignore=shutil.ignore_patterns("__pycache__","*.pyc")); n+=1
print("installés",n)
P
for s in marketing-content-creation website-builder; do [ -d /mnt/user-data/outputs/$s ] && cp -rn /mnt/user-data/outputs/$s "$T/"; done
rm -rf "$W"; echo "total $(ls "$T" | wc -l)"
