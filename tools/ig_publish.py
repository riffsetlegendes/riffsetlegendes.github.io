#!/usr/bin/env python3
"""Publie le carrousel Instagram du jour via l'API officielle d'Instagram.

Usage (dans GitHub Actions) : python3 tools/ig_publish.py jour|focus [--dry-run]
Variables d'environnement : IG_TOKEN (jeton Instagram longue durée), GITHUB_REPOSITORY, GITHUB_TOKEN.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
# Deux variantes possibles du jeton :
#  - connexion Instagram (commence par « IG ») : graph.instagram.com
#  - connexion Facebook (commence par « EAA ») : graph.facebook.com, compte Instagram relié à une Page
FB = os.environ.get("IG_TOKEN", "").strip().startswith("EAA")
API = "https://graph.facebook.com/v21.0" if FB else "https://graph.instagram.com"
MEDIA_BRANCH = "ig-media"


def log(msg):
    print(msg, flush=True)


def call(method, path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode())
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Erreur API Instagram ({e.code}) : {e.read().decode()}")


def sh(*cmd, cwd=None):
    subprocess.run(cmd, check=True, cwd=cwd)


def upload_images(folder, key):
    """Pousse les JPEG sur la branche ig-media et renvoie leurs URL publiques."""
    repo = os.environ["GITHUB_REPOSITORY"]
    work = Path("/tmp/ig-media")
    if work.exists():
        sh("rm", "-rf", str(work))
    remote = f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{repo}.git"
    try:
        sh("git", "clone", "-q", "--depth", "1", "--branch", MEDIA_BRANCH, remote, str(work))
    except subprocess.CalledProcessError:
        work.mkdir(parents=True)
        sh("git", "init", "-q", "-b", MEDIA_BRANCH, cwd=work)
        sh("git", "remote", "add", "origin", remote, cwd=work)
    dest = work / key
    dest.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    names = []
    for png in sorted(folder.glob("*.png")):
        name = png.stem + ".jpg"
        Image.open(png).convert("RGB").save(dest / name, "JPEG", quality=92)
        names.append(name)
    sh("git", "add", "-A", cwd=work)
    sh("git", "-c", "user.name=Riffs & Légendes", "-c", "user.email=bot@users.noreply.github.com",
       "commit", "-q", "--allow-empty", "-m", f"Images Instagram {key}", cwd=work)
    sh("git", "push", "-q", "origin", MEDIA_BRANCH, cwd=work)
    base = f"https://raw.githubusercontent.com/{repo}/{MEDIA_BRANCH}/{key}/"
    urls = [base + n for n in names]
    for u in urls:  # attendre que les fichiers soient servis
        for _ in range(30):
            try:
                with urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=20) as r:
                    if r.status == 200:
                        break
            except Exception:
                pass
            time.sleep(4)
    return urls


def main():
    kind = sys.argv[1]
    dry = "--dry-run" in sys.argv
    today = dt.datetime.now(ZoneInfo("Europe/Paris")).date().isoformat()
    key = f"{today}-{kind}"
    spec = ROOT / "instagram" / f"{key}.json"
    done = ROOT / "instagram" / "publies" / f"{key}.txt"
    if not spec.exists():
        log(f"Pas de carrousel prévu pour {key}.")
        return
    if done.exists() and not dry:
        log(f"Le carrousel {key} est déjà publié.")
        return
    sh(sys.executable, str(ROOT / "tools" / "instagram.py"), str(spec))
    folder = ROOT / "out" / "instagram" / key
    caption = (folder / "legende.txt").read_text(encoding="utf-8").strip()
    urls = upload_images(folder, key)
    log("Images en ligne :\n" + "\n".join(urls))
    if dry:
        log("Essai à blanc : rien n'est publié sur Instagram.")
        return
    if FB:
        uid = None
        try:  # jeton de Page
            uid = (call("GET", "me", fields="instagram_business_account").get("instagram_business_account") or {}).get("id")
        except (Exception, SystemExit):
            pass
        if not uid:  # jeton utilisateur : on cherche la Page reliée à Instagram
            for pg in call("GET", "me/accounts", fields="instagram_business_account,name").get("data", []):
                if pg.get("instagram_business_account"):
                    uid = pg["instagram_business_account"]["id"]
                    break
        if not uid:
            raise SystemExit("Aucun compte Instagram professionnel relié à une Page Facebook n'a été trouvé avec ce jeton.")
    else:
        me = call("GET", "me", fields="user_id,username")
        uid = me.get("user_id") or me.get("id")
    log(f"Compte Instagram : {uid}")
    children = []
    for u in urls:
        r = call("POST", f"{uid}/media", image_url=u, is_carousel_item="true")
        children.append(r["id"])
    carousel = call("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    for _ in range(30):
        st = call("GET", carousel, fields="status_code").get("status_code")
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise SystemExit("Instagram a refusé le carrousel (status ERROR).")
        time.sleep(5)
    post = call("POST", f"{uid}/media_publish", creation_id=carousel)
    log(f"Publié sur Instagram : {post}")
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(json.dumps(post) + "\n", encoding="utf-8")
    sh("git", "add", str(done), cwd=ROOT)
    sh("git", "-c", "user.name=Riffs & Légendes", "-c", "user.email=bot@users.noreply.github.com",
       "commit", "-q", "-m", f"Instagram publié : {key}", cwd=ROOT)
    sh("git", "pull", "-q", "--rebase", "origin", "main", cwd=ROOT)
    sh("git", "push", "-q", "origin", "HEAD:main", cwd=ROOT)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            msg = str(e.code).replace(os.environ.get("IG_TOKEN", "§"), "***").replace("\n", " ")[:900]
            print(f"::error title=Instagram::{msg}", flush=True)
        raise
    except Exception as e:
        msg = repr(e).replace(os.environ.get("IG_TOKEN", "§"), "***")[:900]
        print(f"::error title=Instagram::{msg}", flush=True)
        raise
