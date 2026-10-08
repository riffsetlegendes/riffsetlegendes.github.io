"""Playlist encyclopédique Riffs & Légendes sur Spotify.
  setup        : écrit la page d'autorisation (spotify/index.html) avec le Client ID
  auth CODE    : échange le code d'autorisation, garde le jeton chiffré dans spotify/token.enc
  sync         : crée/complète la playlist (morceaux des articles + spotify/encyclopedie.txt), sans doublons
Secrets : SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET."""
import base64, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parent.parent
SP = ROOT / "spotify"
REDIRECT = "https://riffsetlegendes.github.io/spotify/"
SCOPES = "playlist-modify-public playlist-modify-private playlist-read-private ugc-image-upload"
CID, SECRET = os.environ.get("SPOTIFY_CLIENT_ID", "").strip(), os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
NAME = "Riffs & Légendes : l'encyclopédie du rock"
DESC = ("Le rock de 1950 à 1999 et la relève, classé par artiste de A à Z. Tous les morceaux dont on parle sur riffsetlegendes.github.io, "
        "et bien plus. Mise à jour chaque jour.")


AF = ROOT / "spotify" / "artists.json"
ARTISTS = json.loads(AF.read_text(encoding="utf-8")) if AF.exists() else {}


class RateLimited(Exception):
    pass


def fernet():
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(SECRET.encode()).digest()))


def http(method, url, data=None, headers=None, form=False):
    body = None
    headers = dict(headers or {})
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, method=method, headers=headers), timeout=60) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", "5")) + 1
                if wait > 120:
                    BUDGET["left"] = 0
                    raise RateLimited(wait)
                time.sleep(wait)
                continue
            if e.code >= 500 and attempt < 5:
                time.sleep(3)
                continue
            raise SystemExit(f"Spotify {e.code} sur {url.split('?')[0]} : {e.read().decode()[:400]}")


def basic():
    return {"Authorization": "Basic " + base64.b64encode(f"{CID}:{SECRET}".encode()).decode()}


def setup():
    SP.mkdir(exist_ok=True)
    auth = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
        {"client_id": CID, "response_type": "code", "redirect_uri": REDIRECT, "scope": SCOPES})
    (SP / "index.html").write_text(f"""<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Connexion Spotify | Riffs & Légendes</title>
<style>body{{font-family:system-ui,sans-serif;background:#151b5e;color:#f1f1eb;display:grid;place-items:center;min-height:100vh;margin:0;padding:24px}}
main{{max-width:560px}}a.b{{display:inline-block;background:#f5bf1d;color:#151b5e;padding:14px 22px;font-weight:700;text-decoration:none;border-radius:4px}}
code{{display:block;background:#0b0c18;padding:14px;word-break:break-all;margin:12px 0;user-select:all;border-radius:4px}}</style>
<main><h1>Relier Spotify à Riffs & Légendes</h1><div id="x"></div></main>
<script>var c=new URLSearchParams(location.search).get('code'),e=new URLSearchParams(location.search).get('error'),x=document.getElementById('x');
if(c){{x.innerHTML='<p>C\\'est autorisé. Copie ce code et envoie-le à Claude (il ne sert qu\\'une fois et expire dans 10 minutes) :</p><code>'+c+'</code>';}}
else if(e){{x.innerHTML='<p>Autorisation refusée ('+e+'). Tu peux réessayer.</p><p><a class="b" href="{auth}">Autoriser Spotify</a></p>';}}
else{{x.innerHTML='<p>Un clic suffit : connecte-toi à Spotify et accepte que Riffs & Légendes gère ses playlists sur ton compte.</p><p><a class="b" href="{auth}">Autoriser Spotify</a></p>';}}</script></html>""", encoding="utf-8")
    print("Page d'autorisation prête")


def auth(code):
    tok = http("POST", "https://accounts.spotify.com/api/token",
               {"grant_type": "authorization_code", "code": code.strip(), "redirect_uri": REDIRECT}, basic(), form=True)
    (SP / "token.enc").write_bytes(fernet().encrypt(tok["refresh_token"].encode()))
    print("Jeton Spotify enregistré (chiffré)")


def access():
    rt = fernet().decrypt((SP / "token.enc").read_bytes()).decode()
    tok = http("POST", "https://accounts.spotify.com/api/token", {"grant_type": "refresh_token", "refresh_token": rt}, basic(), form=True)
    if tok.get("refresh_token"):
        (SP / "token.enc").write_bytes(fernet().encrypt(tok["refresh_token"].encode()))
    return {"Authorization": "Bearer " + tok["access_token"]}


def site_tracks():
    """IDs Spotify cités sur le site, dans l'ordre chronologique des morceaux (année)."""
    out = []
    for md in sorted((ROOT / "content").glob("*.md")):
        for block in re.findall(r":::(?:ecoute|tracklist)\n(.*?)\n:::", md.read_text(encoding="utf-8"), re.S):
            for line in block.splitlines():
                cols = [c.strip() for c in line.split("|")]
                if len(cols) >= 4 and re.fullmatch(r"[A-Za-z0-9]{22}", cols[3]):
                    y = re.search(r"\d{4}", cols[2])
                    out.append((sort_key(cols[1]), int(y.group()) if y else 2100, cols[3]))
    return out


def sort_key(artist):
    """Ordre alphabétique par artiste, comme dans un bac de disquaire (sans « The », « Les », « Le », « La »)."""
    a = artist.strip().casefold()
    a = re.sub(r"^(the|les|le|la|l')\s*", "", a)
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", a) if unicodedata.category(c) != "Mn")


BUDGET = {"left": int(os.environ.get("SPOTIFY_SEARCH_BUDGET", "300")), "t0": time.time()}


def resolve(h, line, cache):
    """« année | artiste | titre » -> ID Spotify (recherche), mis en cache. Budget limité par exécution."""
    if line in cache:
        return cache[line]
    if BUDGET["left"] <= 0 or time.time() - BUDGET["t0"] > 1200:
        return None  # sera cherché à la prochaine exécution
    BUDGET["left"] -= 1
    y, artist, title = [c.strip() for c in line.split("|")][:3]
    q = f'track:"{title}" artist:"{artist}"'
    r = http("GET", "https://api.spotify.com/v1/search?" + urllib.parse.urlencode({"q": q, "type": "track", "limit": 5, "market": "FR"}), headers=h)
    best = None
    for t in r.get("tracks", {}).get("items", []):
        names = " ".join(a["name"].lower() for a in t["artists"])
        tn = t["name"].lower()
        if artist.lower().split(" ")[0] in names and not re.search(r"\b(live|karaoke|cover|remix|instrumental)\b", tn):
            best = t["id"]
            ARTISTS.setdefault(artist, t["artists"][0]["id"])
            break
    cache[line] = best
    return best


def sync():
    h = access()
    state_f = SP / "state.json"
    state = json.loads(state_f.read_text()) if state_f.exists() else {"playlist": None, "added": [], "cache": {}}
    if not state.get("playlist"):
        pl = http("POST", "https://api.spotify.com/v1/me/playlists", {"name": NAME, "description": DESC, "public": True}, h)
        state["playlist"] = pl["id"]
        print("Playlist créée :", pl["external_urls"]["spotify"])
    wanted = []
    enc = SP / "encyclopedie.txt"
    if enc.exists():
        lines = [l for l in enc.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#") and l.count("|") >= 2]
        for l in lines:
            cols = [c.strip() for c in l.split("|")]
            y = re.search(r"\d{4}", cols[0])
            try:
                tid = resolve(h, l, state["cache"])
            except RateLimited as rl:
                print(f"Limite Spotify atteinte (attente demandée {rl.args[0]} s), suite à la prochaine exécution")
                tid = None
            if tid:
                wanted.append((sort_key(cols[1]), int(y.group()) if y else 2100, tid))
    wanted += site_tracks()
    wanted.sort(key=lambda x: (x[0], x[1]))
    seen, order = set(), []
    for _, _, tid in wanted:
        if tid not in seen:
            seen.add(tid)
            order.append(tid)
    state_f.write_text(json.dumps(state, ensure_ascii=False, indent=0))
    AF.write_text(json.dumps(ARTISTS, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    if order != state["added"]:  # on réécrit la playlist entière pour garder l'ordre alphabétique
        uris = ["spotify:track:" + t for t in order]
        http("PUT", f"https://api.spotify.com/v1/playlists/{state['playlist']}/items", {"uris": uris[:100]}, h)
        for i in range(100, len(uris), 100):
            http("POST", f"https://api.spotify.com/v1/playlists/{state['playlist']}/items", {"uris": uris[i:i + 100]}, h)
    new = [t for t in order if t not in set(state["added"])]
    state["added"] = order
    state_f.write_text(json.dumps(state, ensure_ascii=False, indent=0))
    miss = sum(1 for v in state["cache"].values() if not v)
    print(f"{len(new)} morceaux ajoutés, {len(state['added'])} au total, {miss} introuvables. https://open.spotify.com/playlist/{state['playlist']}")


def _main():
    cmd = sys.argv[1]
    if not CID or not SECRET:
        raise SystemExit("Secrets SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET manquants")
    if cmd == "setup":
        setup()
    elif cmd == "auth":
        auth(sys.argv[2])
    else:
        sync()


if __name__ == "__main__":
    try:
        _main()
    except BaseException as e:
        if not (isinstance(e, SystemExit) and e.code in (None, 0)):
            print(f"::error title=Spotify::{str(e)[:800]}".replace("\n", " "), flush=True)
        raise
