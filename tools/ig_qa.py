#!/usr/bin/env python3
"""
ig_qa.py - contrôle qualité des Reels « recit » de Riffs & Légendes, avant commit.

Adapté au français et au format maison à partir du pack MIT « instagram-agent-skill »
de Jake Schincariol (hookscore.py, beats.py, caption.py, humanize.py/detect.py) :
mêmes idées, règles réécrites pour nos JSON et pour REELS.md / CHARTE.md.

Ce que ça vérifie, sans réseau :
  - structure du JSON (champs obligatoires, longueurs, 5 hashtags, photos distinctes) ;
  - l'accroche (phrase 1) : longueur, élément concret au début, ouvertures molles,
    date seule en ouverture, préambule ;
  - le rythme : une phrase trop longue = une photo fixe trop longtemps à l'écran ;
  - la relance au milieu, la question finale = cta ;
  - la fenêtre de la légende (les ~125 caractères visibles avant « ... plus ») ;
  - tics d'écriture IA en français, tirets cadratins, caractères invisibles ;
  - règle de la charte : aucune comparaison relève / anciens ;
  - chiffres de la narration absents de l'article du jour (--content content/).

Ce que ça ne fait PAS : prédire les vues. Ça élimine les Reels faibles avant le rendu ;
la rétention mesurée dans Metricool reste le seul juge (bilan du lundi).

Usage
  python3 tools/ig_qa.py instagram/2026-11-07-*.json --content content
  python3 tools/ig_qa.py instagram/2026-11-07-jour.json --fix   # nettoie typo + invisibles
  python3 tools/ig_qa.py content/2026-11-07-*.md                 # articles : tics, typo, charte
Code de sortie 1 s'il reste un ÉCHEC (à corriger avant commit).
"""

import argparse
import glob
import json
import os
import re
import sys
import unicodedata

FIN_LEGENDE = "L'histoire complète est sur riffsetlegendes.github.io, lien en bio."
FENETRE = 125            # caractères visibles de la légende dans le fil
MOTS_PAR_SECONDE = 2.2   # rythme des sous-titres (synthèse ralentie à -12 %)

INVISIBLES = {
    "​", "‌", "‍", "⁠", "­", "﻿", "⁣",
    "⁢", "⁡", "᠎", "‎", "‏",
}
# Espaces insécables : légitimes en typographie française, mais Instagram les
# affiche mal dans certaines polices ; on les remplace par une espace simple.
ESPACES = {" ": " ", " ": " ", " ": " "}

NOMBRES_DITS = {
    "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
    "onze", "douze", "quinze", "vingt", "trente", "quarante", "cinquante",
    "soixante", "cent", "cents", "mille", "million", "millions", "milliard",
    "moitié", "double", "triple", "dernier", "dernière", "seul", "seule",
}
OUVERTURES_MOLLES = [
    "aujourd'hui", "bonjour", "salut", "hello", "dans cette vidéo", "dans ce reel",
    "on va", "je vais", "il était une fois", "vous connaissez", "tu connais",
    "le saviez-vous", "saviez-vous", "retour sur", "joyeux anniversaire",
    "petit rappel", "zoom sur", "focus sur", "parlons de", "voici",
    "c'est l'histoire", "connaissez-vous", "est-ce que",
]
PREAMBULES = re.compile(
    r"(?i)\b(dans (cette|la) vidéo|je vais vous (montrer|raconter)|on va (voir|parler)|"
    r"reste jusqu'à la fin|regarde jusqu'au bout|arrête de scroller|ne scrolle pas)\b")
DATE_OUVERTURE = re.compile(
    r"(?i)^\s*(le\s+)?(\d{1,2}(er)?\s+)?(janvier|février|mars|avril|mai|juin|juillet|"
    r"août|septembre|octobre|novembre|décembre)\s+\d{4}\s*[,:.]")
RELANCES = re.compile(
    r"(?i)^\s*(mais|problème|sauf que|pourtant|seul hic|le hic|sauf qu|or,|"
    r"résultat|surprise|et là|personne ne|ce que personne)")

# Tics d'écriture « IA » en français (signalés, pas remplacés : la reformulation
# demande du jugement). Ajoute ou retire librement.
TICS = [
    "emblématique", "incontournable", "iconique", "intemporel", "intemporelle",
    "véritable", "plongez", "plongeons", "plongée dans", "à couper le souffle",
    "sans précédent", "a révolutionné", "révolutionner", "a marqué l'histoire",
    "marqué à jamais", "à jamais", "entré dans la légende", "entrée dans la légende",
    "gravé dans les mémoires", "restera gravé", "une page se tourne",
    "héritage indélébile", "empreinte indélébile", "laisse une empreinte",
    "nul doute", "force est de constater", "il faut dire que", "en somme",
    "en effet", "par ailleurs", "de plus,", "au fil des", "tout simplement",
    "fascinant", "fascinante", "captivant", "captivante", "magistral",
    "un tournant décisif", "véritable ovni", "bien plus qu'", "plus qu'un simple",
    "à l'aube de", "dans l'ombre de", "pierre angulaire", "symphonie de",
    "tapisserie", "odyssée", "voyage sonore", "chef-d'œuvre absolu",
    "abonne-toi", "abonnez-vous", "like si", "partage si", "tag un pote",
    "identifie un pote", "n'oublie pas de", "lien dans la bio pour",
]
STRUCTURES = [
    (re.compile(r"(?i)\bce n'est pas (seulement |juste |qu')?[^.!?]{2,60}[,.] c'est\b"),
     "« Ce n'est pas X, c'est Y » : dis directement Y."),
    (re.compile(r"(?i)\bnon seulement\b[^.!?]{2,80}\bmais (aussi|encore)\b"),
     "« Non seulement… mais aussi » : coupe en deux phrases ou garde la plus forte."),
    (re.compile(r"(?i)\bplus qu'un(e)? [^.!?]{2,40}, (c'est|un|une)\b"),
     "« Plus qu'un X, c'est Y » : formule creuse."),
]
# Charte : jamais de comparaison relève / anciens.
COMPARAISONS = re.compile(
    r"\b([Hh]éritiers? d[eu']|[Dd]ans la lignée d|[Dd]ignes? successeurs?|[Ff]ils spirituels?|"
    r"(?:rappelle(?:nt)?|sonne(?:nt)? comme|à la manière d[eu']|"
    r"les nouveaux|le nouveau|la nouvelle) (?:les |le |la |l')?[A-ZÉ])")


def mots(t):
    return re.findall(r"[\wÀ-ÿ'’-]+", t)


def phrases(t):
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", t.strip()) if p.strip()]


def concret(t, debut=None):
    """Un élément concret : chiffre, nombre dit, nom propre (hors 1er mot), guillemets."""
    w = mots(t)
    if debut:
        w = w[:debut]
        t = " ".join(w)
    if re.search(r"\d", t) or "«" in t:
        return True
    if any(x.lower() in NOMBRES_DITS for x in w):
        return True
    return any(x[:1].isupper() and len(x) > 2 for x in w[1:])


class Rapport:
    def __init__(self, nom):
        self.nom, self.lignes, self.echecs, self.alertes = nom, [], 0, 0

    def ok(self, quoi, detail=""):
        self.lignes.append(("OK", quoi, detail))

    def alerte(self, quoi, detail):
        self.alertes += 1
        self.lignes.append(("ALERTE", quoi, detail))

    def echec(self, quoi, detail):
        self.echecs += 1
        self.lignes.append(("ÉCHEC", quoi, detail))


def textes(d):
    out = [d.get("title", ""), d.get("caption", ""), d.get("cta", "")]
    out += [n.get("text", "") for n in d.get("narration", [])]
    return out


def nettoyer(t):
    for c in INVISIBLES:
        t = t.replace(c, "")
    for a, b in ESPACES.items():
        t = t.replace(a, b)
    t = re.sub(r"\s*—\s*", ", ", t)
    t = re.sub(r"(?<=\w)\s–\s(?=\w)", ", ", t)
    t = t.replace("’", "'").replace("…", "...")
    return re.sub(r" {2,}", " ", t)


def article_du_jour(content, date):
    if not content:
        return None
    txt = ""
    for f in glob.glob(os.path.join(content, f"{date}-*.md")):
        txt += open(f, encoding="utf-8").read()
    return txt or None


def controler(path, content=None):
    d = json.load(open(path, encoding="utf-8"))
    r = Rapport(os.path.basename(path))
    narr = d.get("narration", [])
    nt = [n.get("text", "") for n in narr]

    # Structure
    if d.get("format") != "recit" or d.get("reel") is not True:
        r.echec("FORMAT", '"format": "recit" et "reel": true attendus')
    for champ in ("label", "big", "title", "song", "caption", "hashtags", "photos"):
        if not d.get(champ):
            r.echec("CHAMP", f'"{champ}" manquant')
    if "voice_on" in d and d["voice_on"]:
        r.echec("VOIX", "voice_on interdit sans accord de Yann (REELS.md §2)")
    if not d.get("audio_id"):
        r.alerte("SON", "pas d'audio_id : la recherche automatique risque une reprise ou un mauvais titre")
    if not d.get("hook_formule"):
        r.alerte("ACCROCHE", 'champ "hook_formule" absent (REELS.md §8), utile au bilan du lundi')
    t = d.get("title", "")
    (r.echec if len(t) > 30 else r.ok)("TITRE", f"{len(t)}/30 car. « {t} »")

    if not 7 <= len(narr) <= 9:
        r.echec("NARRATION", f"{len(narr)} phrases (7 à 9 attendues)")
    total = sum(len(mots(x)) for x in nt)
    if not 80 <= total <= 110:
        r.alerte("LONGUEUR", f"{total} mots (80 à 110 attendus) ≈ {total / MOTS_PAR_SECONDE:.0f} s")
    else:
        r.ok("LONGUEUR", f"{total} mots ≈ {total / MOTS_PAR_SECONDE:.0f} s")

    # Photos
    ph = d.get("photos", [])
    if len(set(ph)) != len(ph):
        r.echec("PHOTOS", "doublons dans photos")
    if not 6 <= len(ph) <= 8:
        r.alerte("PHOTOS", f"{len(ph)} photos (6 à 8 attendues)")
    idx = [n.get("photo") for n in narr]
    if any(i is None or not isinstance(i, int) or i >= len(ph) for i in idx):
        r.echec("PHOTOS", "index de photo invalide dans narration")
    elif len(set(idx)) < len(idx):
        r.alerte("PHOTOS", "la même photo revient pour deux phrases : une photo par phrase")
    for u in ph:
        if re.search(r"lookaside\.|fbsbx|instagram\.f|scontent", u):
            r.echec("PHOTOS", f"URL interdite (expire ou bloquée) : {u[:60]}")

    # Accroche
    if nt:
        h = nt[0]
        n = len(mots(h))
        if n > 16:
            r.echec("ACCROCHE", f"{n} mots : illisible en 2 secondes. Coupe sous 12.")
        elif n > 12:
            r.alerte("ACCROCHE", f"{n} mots, vise 12 maximum")
        if not concret(h, debut=6) and not h.rstrip().endswith("?"):
            r.alerte("ACCROCHE", "rien de concret dans les 6 premiers mots (nom, nombre, objet) ni question")
        low = h.lower().lstrip("« \"")
        for o in OUVERTURES_MOLLES:
            if low.startswith(o):
                r.echec("ACCROCHE", f"ouverture molle « {o} » : ouvre sur le fait étrange")
        if DATE_OUVERTURE.search(h):
            r.alerte("ACCROCHE", "date seule en ouverture : la date vient en phrase 2 (SWIPE.md)")
        if PREAMBULES.search(h):
            r.echec("ACCROCHE", "préambule de vidéo : supprime-le")
        if not any(l[0] != "OK" and l[1] == "ACCROCHE" for l in r.lignes):
            r.ok("ACCROCHE", f"« {h} »")

    # Rythme (beats.py) : une phrase longue = une photo fixe trop longtemps
    for i, x in enumerate(nt[1:], 2):
        s = len(mots(x)) / MOTS_PAR_SECONDE
        if s > 8:
            r.alerte("RYTHME", f"phrase {i} ≈ {s:.0f} s sur une seule photo : coupe-la en deux")
    milieu = nt[2:-1] if len(nt) > 3 else []
    if milieu and not any(RELANCES.search(x) for x in milieu):
        r.alerte("RELANCE", "aucune relance au milieu (« Mais… », « Problème : », retournement)")

    # Question finale
    cta = d.get("cta", "")
    suspense = d.get("test") == "suspense"  # REELS.md §10 : fin en renvoi vers le site, pas de question
    if nt and not suspense and not nt[-1].rstrip().endswith("?"):
        r.echec("QUESTION", "la dernière phrase doit être la question au spectateur")
    if cta and nt and cta.strip().lower() not in nt[-1].strip().lower():
        r.alerte("QUESTION", "cta différent de la dernière phrase de la narration")
    if len(cta) > 60:
        r.echec("QUESTION", f"cta {len(cta)}/60 car.")

    # Légende (caption.py)
    cap = d.get("caption", "")
    ps = phrases(cap)
    if not cap.strip().endswith(FIN_LEGENDE):
        r.echec("LÉGENDE", "doit finir par : " + FIN_LEGENDE)
    if not 3 <= len(ps) <= 6:
        r.alerte("LÉGENDE", f"{len(ps)} phrases (3 à 5 + la phrase de fin)")
    if cta and not suspense and cta not in cap:
        r.alerte("LÉGENDE", "la question finale n'est pas reprise dans la légende")
    if ps and len(ps[0]) > FENETRE:
        r.alerte("LÉGENDE", f"1re phrase {len(ps[0])} car. : coupée par « ... plus » avant la fin")
    if nt and ps and ps[0].strip().lower() == nt[0].strip().lower():
        r.alerte("LÉGENDE", "1re phrase identique à l'accroche : reformule")
    fen = cap[:FENETRE]
    r.ok("FENÊTRE", f"« {fen}… plus »")

    tags = d.get("hashtags", [])
    if len(tags) != 5:
        r.echec("HASHTAGS", f"{len(tags)} (exactement 5)")
    if "riffsetlegendes" not in tags:
        r.echec("HASHTAGS", "riffsetlegendes manquant")
    if any(x.startswith("#") or " " in x or x != x.lower() for x in tags):
        r.alerte("HASHTAGS", "sans #, sans espace, en minuscules")

    # Tics IA, typographie, invisibles, charte
    tout = "\n".join(textes(d))
    inv = sorted({f"U+{ord(c):04X}" for c in tout if c in INVISIBLES or (unicodedata.category(c) == "Cf" and c not in "\n")})
    if inv:
        r.echec("INVISIBLES", ", ".join(inv) + " (--fix pour nettoyer)")
    if "—" in tout:
        r.alerte("TYPO", f"{tout.count('—')} tiret(s) cadratin(s) (--fix)")
    trouves = [w for w in TICS if re.search(r"(?i)(?<![\wÀ-ÿ])" + re.escape(w), tout)]
    if trouves:
        r.alerte("TICS IA", ", ".join(trouves))
    for rx, msg in STRUCTURES:
        if rx.search(tout):
            r.alerte("TICS IA", msg)
    m = COMPARAISONS.search(tout)
    if m:
        r.alerte("CHARTE", f"comparaison relève/anciens ? « {m.group(0)} » (vérifie le contexte)")

    # Chiffres vérifiés dans l'article du jour
    date = os.path.basename(path)[:10]
    art = article_du_jour(content, date)
    if content and art is None:
        r.alerte("FAITS", f"aucun article {date}-*.md dans {content}")
    elif art:
        manq = [x for x in sorted(set(re.findall(r"\d[\d  .]*\d|\d", " ".join(nt)))) if x.replace(" ", "").replace(" ", "") not in art.replace(" ", "").replace(" ", "")]
        if manq:
            r.alerte("FAITS", "chiffres absents des articles du jour : " + ", ".join(manq))
    return r


def controler_article(path):
    """Articles .md : seulement tics IA, typographie, invisibles et charte."""
    r = Rapport(os.path.basename(path))
    tout = open(path, encoding="utf-8").read()
    corps = tout.split("---", 2)[-1]
    corps = re.sub(r":::(ecoute|thisis)[\s\S]*?:::", "", corps)
    inv = sorted({f"U+{ord(c):04X}" for c in corps if c in INVISIBLES})
    if inv:
        r.echec("INVISIBLES", ", ".join(inv))
    n = corps.count("—")
    if n > 2:
        r.alerte("TYPO", f"{n} tirets cadratins (CHARTE : pas en rafale)")
    trouves = [w for w in TICS if re.search(r"(?i)(?<![\wÀ-ÿ])" + re.escape(w), corps)]
    if len(trouves) >= 2:
        r.alerte("TICS IA", ", ".join(trouves))
    for rx, msg in STRUCTURES:
        if rx.search(corps):
            r.alerte("TICS IA", msg)
    m = COMPARAISONS.search(corps)
    if m:
        r.alerte("CHARTE", f"comparaison relève/anciens ? « {m.group(0)} » (vérifie le contexte)")
    return r


def corriger(path):
    d = json.load(open(path, encoding="utf-8"))

    def rec(o):
        if isinstance(o, str):
            return nettoyer(o) if not o.startswith("http") else o
        if isinstance(o, list):
            return [rec(x) for x in o]
        if isinstance(o, dict):
            return {k: rec(v) for k, v in o.items()}
        return o
    d2 = rec(d)
    if d2 != d:
        json.dump(d2, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(path, "a", encoding="utf-8").write("\n")
        return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fichiers", nargs="+")
    ap.add_argument("--content", help="dossier des articles (content/) pour vérifier les chiffres")
    ap.add_argument("--fix", action="store_true", help="nettoie invisibles, tirets cadratins, apostrophes")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--court", action="store_true", help="n'affiche que alertes et échecs")
    a = ap.parse_args()
    fichiers = [f for f in a.fichiers if not os.path.basename(f).startswith(("exemple", "zz-"))]
    res, bilan = [], 0
    for f in fichiers:
        if f.endswith(".md"):
            r = controler_article(f)
            res.append(r)
            bilan |= 1 if r.echecs else 0
            continue
        if a.fix and corriger(f):
            print(f"nettoyé : {f}")
        r = controler(f, a.content)
        res.append(r)
        bilan |= 1 if r.echecs else 0
    if a.json:
        print(json.dumps([{"fichier": r.nom, "echecs": r.echecs, "alertes": r.alertes,
                           "lignes": r.lignes} for r in res], ensure_ascii=False, indent=1))
    else:
        for r in res:
            etat = "À CORRIGER" if r.echecs else ("À REVOIR" if r.alertes else "PRÊT")
            print(f"\n{r.nom}  ·  {etat}  ·  {r.echecs} échec(s), {r.alertes} alerte(s)")
            print("-" * 72)
            for niveau, quoi, det in r.lignes:
                if a.court and niveau == "OK":
                    continue
                print(f"  {niveau:<7}{quoi:<12}{det}")
    sys.exit(bilan)


if __name__ == "__main__":
    main()
