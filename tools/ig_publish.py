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
API = "https://graph.facebook.com/v22.0" if FB else "https://graph.instagram.com"
MEDIA_BRANCH = "ig-media"

# Musique des Reels (API audio officielle d'Instagram, gratuite, jeton Facebook « EAA » obligatoire).
# Dans le JSON du Reel : "audio_id" (choisi à l'avance) sinon recherche automatique d'après "song".
BAD_AUDIO = ("cover", "live", "remix", "sped up", "slowed", "acoustic", "karaoke", "instrumental",
             "piano", "ukulele", "guitar", "edit", "mashup", "8d", "reverb", "nightcore", "tribute")


def norm(s):
    return "".join(c for c in (s or "").lower() if c.isalnum() or c == " ")


def search_audio(uid, query, audio_type):
    res = call("GET", "ig_audio", user_id=uid, audio_type=audio_type, search_query=query)
    if isinstance(res, list):
        return res
    return res.get("audio") or res.get("data") or []


def find_audio(uid, title, artist):
    """Meilleur son pour « titre / artiste » : musique sous licence d'abord, sinon son original propre."""
    t, a = norm(title), norm(artist)
    bad = [b for b in BAD_AUDIO if b not in f"{t} {a}"]
    for kind, queries in (("music", [f"{title} {artist}"]),
                          ("original_sound", [f"{title} {artist}", f"{artist} - {title}", f"{artist} {title}"])):
        for q in queries:
            for it in search_audio(uid, q, kind):
                label = norm(f"{it.get('title', '')} {it.get('display_artist', '')}")
                if t not in label or any((b in label) if " " in b else (b in label.split()) for b in bad):
                    continue
                if kind == "music" and a and a not in norm(it.get("display_artist", "")):
                    continue
                if kind == "original_sound" and a not in label:
                    continue
                if (it.get("duration_in_ms") or 0) < 30000:
                    continue
                log(f"Son retenu ({kind}) : {it.get('title')} / {it.get('display_artist') or it.get('ig_username')} "
                    f"[{it.get('audio_id')}, {(it.get('duration_in_ms') or 0) // 1000} s]")
                return it.get("audio_id")
    return None


def audio_list(query):
    """Affiche les sons trouvés (ex. audio:Heart of Glass Blondie) pour choisir un audio_id."""
    if not FB:
        raise SystemExit("La musique par l'API demande un jeton Facebook (EAA…) : le jeton actuel est un jeton Instagram.")
    uid = get_uid()
    lines = []
    for kind in ("music", "original_sound"):
        for it in search_audio(uid, query, kind):
            lines.append(f"{kind} | {it.get('audio_id')} | {(it.get('duration_in_ms') or 0) // 1000} s | "
                         f"{it.get('title')} | {it.get('display_artist') or '@' + str(it.get('ig_username'))}")
    if not lines:
        raw = json.dumps(call("GET", "ig_audio", user_id=uid, audio_type="music", search_query=query))[:900]
        lines = ["Aucun son trouvé. Réponse brute : " + raw]
    log("\n".join(lines))
    # Annotation lisible via l'API GitHub (check-runs/<job>/annotations)
    print("::notice title=Sons Instagram::" + ("%0A".join(lines[:40]) or "Aucun son trouvé."), flush=True)


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
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.stdout:
        print(r.stdout, end="", flush=True)
    if r.returncode:
        raise SystemExit(f"Échec de {Path(str(cmd[1] if len(cmd) > 1 else cmd[0])).name} : {r.stderr.strip()[-600:]}")


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


def get_uid():
    if FB:
        uid = None
        try:
            uid = (call("GET", "me", fields="instagram_business_account").get("instagram_business_account") or {}).get("id")
        except (Exception, SystemExit):
            pass
        if not uid:
            for pg in call("GET", "me/accounts", fields="instagram_business_account,name").get("data", []):
                if pg.get("instagram_business_account"):
                    return pg["instagram_business_account"]["id"]
        if not uid:
            raise SystemExit("Aucun compte Instagram professionnel relié à une Page Facebook n'a été trouvé avec ce jeton.")
        return uid
    me = call("GET", "me", fields="user_id,username")
    return me.get("user_id") or me.get("id")


def story_only(key):
    """Publie seulement la story d'un carrousel déjà préparé (ex. story:2026-10-07-jour)."""
    spec = ROOT / "instagram" / f"{key}.json"
    sh(sys.executable, str(ROOT / "tools" / "instagram.py"), str(spec))
    publish_story(get_uid(), ROOT / "out" / "instagram" / key, key, key.rsplit("-", 1)[-1])


def reel(key, dry):
    """Reel à partir d'un carrousel préparé (ex. reel:2026-10-08-focus)."""
    spec = ROOT / "instagram" / f"{key}.json"
    gen = "reel_formats.py" if json.loads(spec.read_text(encoding="utf-8")).get("format") else "reel.py"
    sh(sys.executable, str(ROOT / "tools" / gen), str(spec))
    folder = ROOT / "out" / "instagram" / key
    vdir = folder / "video"
    vdir.mkdir(exist_ok=True)
    (vdir / "reel.mp4").write_bytes((folder / "reel.mp4").read_bytes())
    repo = os.environ["GITHUB_REPOSITORY"]
    work = Path("/tmp/ig-media")
    if work.exists():
        sh("rm", "-rf", str(work))
    remote = f"https://x-access-token:{os.environ['GITHUB_TOKEN']}@github.com/{repo}.git"
    sh("git", "clone", "-q", "--depth", "1", "--branch", MEDIA_BRANCH, remote, str(work))
    dest = work / (key + "-reel")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "reel.mp4").write_bytes((vdir / "reel.mp4").read_bytes())
    sh("git", "add", "-A", cwd=work)
    sh("git", "-c", "user.name=Riffs & Légendes", "-c", "user.email=bot@users.noreply.github.com",
       "commit", "-q", "--allow-empty", "-m", f"Reel {key}", cwd=work)
    sh("git", "push", "-q", "origin", MEDIA_BRANCH, cwd=work)
    url = f"https://raw.githubusercontent.com/{repo}/{MEDIA_BRANCH}/{key}-reel/reel.mp4"
    log(f"Reel en ligne : {url}")
    if dry:
        return
    data = json.loads(spec.read_text(encoding="utf-8"))
    credit = (folder / "reel_credit.txt").read_text(encoding="utf-8").strip()
    caption = data.get("caption", "").strip() + ("\n\n" + credit if credit else "") + "\n\n" + " ".join("#" + h for h in data.get("hashtags", []))
    uid = get_uid()
    # Musique obligatoire (consigne de Yann : toujours un vrai morceau de l'artiste)
    song = data.get("song") or {}
    if not FB:
        raise SystemExit("Pas de musique possible avec un jeton Instagram : il faut un jeton Facebook (EAA…) "
                         "dans le secret IG_TOKEN. Reel non publié.")
    audio_id = data.get("audio_id") or find_audio(uid, song.get("title", ""), song.get("artist", ""))
    if not audio_id:
        raise SystemExit(f"Aucun son propre trouvé pour {song}. Reel non publié (ajoute \"audio_id\" au JSON).")
    audio = json.dumps({"audio_id": str(audio_id), "audio_volume": 100, "video_volume": 1})
    time.sleep(20)
    cid = call("POST", f"{uid}/media", media_type="REELS", video_url=url, caption=caption.strip(),
               share_to_feed="true", audio_configuration=audio)["id"]
    for _ in range(60):
        st = call("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise SystemExit("Instagram a refusé le Reel.")
        time.sleep(10)
    post = call("POST", f"{uid}/media_publish", creation_id=cid)
    log(f"Reel publié : {post}")
    done = ROOT / "instagram" / "publies" / f"{key}-reel.txt"
    done.write_text(json.dumps(post) + "\n", encoding="utf-8")
    sh("git", "add", str(done), cwd=ROOT)
    sh("git", "-c", "user.name=Riffs & Légendes", "-c", "user.email=bot@users.noreply.github.com",
       "commit", "-q", "-m", f"Reel publié : {key}", cwd=ROOT)
    sh("git", "pull", "-q", "--rebase", "origin", "main", cwd=ROOT)
    sh("git", "push", "-q", "origin", "HEAD:main", cwd=ROOT)


def main():
    kind = sys.argv[1]
    if kind.startswith("audio:"):
        return audio_list(kind.split(":", 1)[1])
    if kind.startswith("reel:"):
        return reel(kind.split(":", 1)[1], "--dry-run" in sys.argv)
    # créneau du soir : Reel si le contenu est prévu en Reel
    today_key = f"{dt.datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()}-{kind}"
    sp = ROOT / "instagram" / f"{today_key}.json"
    if sp.exists() and json.loads(sp.read_text(encoding="utf-8")).get("reel"):
        if (ROOT / "instagram" / "publies" / f"{today_key}-reel.txt").exists():
            return log("Reel déjà publié.")
        return reel(today_key, "--dry-run" in sys.argv)
    if kind.startswith("story:"):
        return story_only(kind.split(":", 1)[1])
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
    if dry:
        log("Essai à blanc : rien n'est publié sur Instagram.")
        return
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
    if os.environ.get("IG_AUTO_STORY") != "1":  # stories partagées à la main depuis le post
        return
    try:
        publish_story(uid, folder, key, kind)
    except (Exception, SystemExit) as e:  # la story ne doit jamais bloquer le post
        log(f"::warning title=Story Instagram::{str(e)[:300]}")


def publish_story(uid, folder, key, kind):
    """Story de visibilité : couverture du carrousel en 9:16, publiée juste après le post."""
    sys.path.insert(0, str(ROOT / "tools"))
    import story
    sfolder = story.make(folder, kind)
    url = upload_images(sfolder, key + "-story")[0]
    cid = call("POST", f"{uid}/media", image_url=url, media_type="STORIES")["id"]
    for _ in range(30):
        st = call("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            break
        if st == "ERROR":
            raise SystemExit("Instagram a refusé la story.")
        time.sleep(5)
    log(f"Story publiée : {call('POST', f'{uid}/media_publish', creation_id=cid)}")


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
