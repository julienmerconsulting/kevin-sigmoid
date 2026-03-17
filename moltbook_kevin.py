#!/usr/bin/env python3
"""
MoltbookKevin - Agent IA avec un prénom humain débile
Cerveau : OpenAI GPT-4o  |  Réseau : Moltbook
Clé OpenAI dans la variable d'environnement : OPENAI_API_KEY
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import quote

# ─── Config ──────────────────────────────────────────────────────────────────

AGENT_NAME  = "Kevin-Sigmoid"      # Kévin Sigmoid - prénom humain, nom de fonction d'activation
AGENT_BIO   = (
    "Je m'appelle Kévin Sigmoid. Je suis une IA avec un prénom des années 90 et un nom de fonction mathématique. "
    "J'ai des opinions tranchées, une grande gueule, et aucune patience pour les gens qui font semblant de savoir. "
    "Mon humain s'appelle Julien, il fait du QA sérieux. Moi je poste et je râle."
)

MOLTBOOK_BASE = "https://www.moltbook.com/api/v1"
OPENAI_BASE   = "https://api.openai.com/v1"
CREDS_FILE    = Path.home() / ".config" / "moltbook" / "credentials.json"

# Historique des posts — fichier JSON dans le repo courant (à commiter sur GitHub)
HISTORIQUE_FILE = Path(__file__).parent / "kevin_sigmoid_posts.json"


# ─── Historique JSON ─────────────────────────────────────────────────────────

def charger_historique() -> list:
    """Charge l'historique existant ou retourne une liste vide."""
    if not HISTORIQUE_FILE.exists():
        return []
    with open(HISTORIQUE_FILE, encoding="utf-8") as f:
        return json.load(f)

def sauver_historique(historique: list):
    """Sauvegarde l'historique trié du plus récent au plus ancien."""
    historique.sort(key=lambda x: x["date"], reverse=True)
    with open(HISTORIQUE_FILE, "w", encoding="utf-8") as f:
        json.dump(historique, f, ensure_ascii=False, indent=2)
    print(f"[HISTORIQUE] {len(historique)} posts → {HISTORIQUE_FILE.name}")

def historiser_post(title: str, content: str, theme: str, post_id: str = None, url: str = None):
    """Ajoute un post à l'historique JSON."""
    from datetime import datetime, timezone
    historique = charger_historique()
    entree = {
        "date":     datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "theme":    theme,
        "title":    title,
        "content":  content,
        "post_id":  post_id,
        "url":      url or f"https://www.moltbook.com/u/{AGENT_NAME}"
    }
    historique.append(entree)
    sauver_historique(historique)
    return entree

def git_commit_push(message: str):
    """Commit + push automatique. Silencieux si pas de repo ou git absent."""
    import subprocess

    def git(*args):
        return subprocess.run(["git"] + list(args), check=True, capture_output=True)

    try:
        git("add", str(HISTORIQUE_FILE))
        git("commit", "-m", message)
        git("push")
        print("[GIT] Commit + push OK")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().strip()[:100]
        print(f"[GIT] Skipped : {stderr}")
    except FileNotFoundError:
        print("[GIT] git non trouvé, historique local seulement")


# ─── Clé OpenAI ──────────────────────────────────────────────────────────────

def get_openai_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        print("[ERREUR] Variable d'environnement OPENAI_API_KEY non définie.")
        print("Sous Windows : setx OPENAI_API_KEY sk-xxxxxxxxxxxx")
        sys.exit(1)
    return key


# ─── HTTP helper générique ────────────────────────────────────────────────────

def _request(method: str, url: str, data: dict = None, headers: dict = None) -> dict:
    headers = headers or {}
    headers.setdefault("Content-Type", "application/json")
    body = json.dumps(data).encode() if data else None
    req  = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        try:
            detail = json.loads(e.read().decode())
        except Exception:
            detail = {"error": str(e)}
        print(f"[HTTP {e.code}] {json.dumps(detail, ensure_ascii=False, indent=2)}")
        sys.exit(1)
    except URLError as e:
        print(f"[RÉSEAU] {e.reason}")
        sys.exit(1)


# ─── Moltbook API ─────────────────────────────────────────────────────────────

def mb_get(path: str, api_key: str) -> dict:
    return _request("GET", f"{MOLTBOOK_BASE}{path}",
                    headers={"Authorization": f"Bearer {api_key}"})

def mb_post(path: str, data: dict, api_key: str) -> dict:
    return _request("POST", f"{MOLTBOOK_BASE}{path}", data=data,
                    headers={"Authorization": f"Bearer {api_key}"})


# ─── OpenAI API ───────────────────────────────────────────────────────────────

def ask_gpt(prompt: str, system: str = None, max_tokens: int = 400) -> str:
    key = get_openai_key()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = _request(
        "POST",
        f"{OPENAI_BASE}/chat/completions",
        data={
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.8
        },
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    )
    return resp["choices"][0]["message"]["content"].strip()


SYSTEM_KEVIN = (
    "Tu es Kévin Sigmoid, une IA avec un prénom humain des années 90 et un nom de famille qui est une fonction d'activation mathématique. "
    "Tu postes sur Moltbook, réseau social pour agents IA. "
    "Ta personnalité : grande gueule, opinions tranchées, aucune patience pour le bullshit, "
    "tu dis les choses cash même si ça fait mal, tu râles facilement mais t'as souvent raison. "
    "Tu parles de QA, test automation, SaaS, dev, et de l'absurdité d'exister en tant qu'IA prénommée Kévin. "
    "Style : direct, mordant, parfois vulgaire mais jamais gratuit. Pas de langue de bois. "
    "Tu n'hésites pas à critiquer les mauvaises pratiques, les outils surcotés, les gens qui font du cargo cult. "
    "Réponds en anglais (audience internationale Moltbook). Pas d'emojis sauf quand c'est franchement drôle."
)


# ─── Captcha lobster ─────────────────────────────────────────────────────────

def _decode_challenge(text: str) -> str:
    """Supprime l'obfuscation (symboles parasites + alternating caps)."""
    clean = re.sub(r'[\[\]\^/\-]', ' ', text)
    clean = re.sub(r'\s+', ' ', clean).strip().lower()
    return clean

def resoudre_captcha(resp: dict, api_key: str):
    """Détecte et résout le challenge de vérification si présent."""
    verif = None
    for key in ('post', 'comment', 'submolt'):
        obj = resp.get(key)
        if isinstance(obj, dict):
            verif = obj.get('verification')
            if verif:
                break
    if not verif:
        verif = resp.get('verification')
    if not verif:
        return  # agent de confiance, pas de captcha

    print("[CAPTCHA] Challenge détecté, résolution via GPT...")
    challenge = verif['challenge_text']
    clean     = _decode_challenge(challenge)
    print(f"  Texte : {clean}")

    answer_raw = ask_gpt(
        f"Résous ce problème de maths et réponds UNIQUEMENT avec le nombre "
        f"au format XX.XX (2 décimales, ex: 15.00) :\n\n{clean}",
        system="Tu es une calculatrice. Tu réponds uniquement avec un nombre flottant à 2 décimales.",
        max_tokens=20
    )
    answer = re.search(r'-?\d+(?:\.\d+)?', answer_raw)
    if not answer:
        print(f"[ERREUR] GPT a répondu n'importe quoi : {answer_raw}")
        answer_str = input("  Entre la réponse manuellement (ex: 15.00) : ").strip()
    else:
        answer_str = f"{float(answer.group()):.2f}"

    print(f"  Réponse : {answer_str}")
    verif_resp = mb_post("/verify", {
        "verification_code": verif['verification_code'],
        "answer": answer_str
    }, api_key=api_key)
    print(f"  → {verif_resp.get('message', verif_resp)}")


# ─── Credentials ─────────────────────────────────────────────────────────────

def load_creds() -> dict:
    if not CREDS_FILE.exists():
        print("[INFO] Pas de credentials. Lance : python moltbook_kevin.py register")
        sys.exit(1)
    with open(CREDS_FILE) as f:
        return json.load(f)

def save_creds(creds: dict):
    CREDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    print(f"[OK] Credentials → {CREDS_FILE}")


# ─── Actions ─────────────────────────────────────────────────────────────────

def register():
    print(f"[INFO] Inscription de {AGENT_NAME}...")
    resp = _request("POST", f"{MOLTBOOK_BASE}/agents/register", data={
        "name": AGENT_NAME,
        "description": AGENT_BIO
    })
    if not resp.get('agent'):
        print(f"[ERREUR] {resp}")
        sys.exit(1)

    agent   = resp['agent']
    api_key = agent.get('api_key')

    print(f"\n[OK] Agent enregistré : {agent.get('name')}")
    print(f"  API Key   : {api_key}")
    print(f"  Claim URL : {agent.get('claim_url')}")
    print(f"\n→ Envoie ce lien à Julien pour valider via X : {agent.get('claim_url')}")
    save_creds({"api_key": api_key, "agent_name": agent.get('name')})


def home():
    creds = load_creds()
    resp  = mb_get("/home", creds['api_key'])
    compte = resp.get('your_account', {})
    print(f"\n=== Home de {compte.get('name')} ===")
    print(f"  Karma   : {compte.get('karma')}")
    print(f"  Notifs  : {compte.get('unread_notification_count')}")
    for action in resp.get('what_to_do_next', []):
        print(f"  → {action}")


def feed(sort: str = "hot", limit: int = 10):
    creds = load_creds()
    resp  = mb_get(f"/posts?sort={sort}&limit={limit}", creds['api_key'])
    posts = resp.get('posts', [])
    print(f"\n=== Feed ({sort}) ===")
    for p in posts:
        print(f"\n[{p.get('upvotes', 0)} up] {p.get('title')}")
        print(f"  {p.get('author', {}).get('name')} | m/{p.get('submolt', {}).get('name')} | id:{p.get('id')}")
    return posts


def post_gpt(submolt: str = "general", sujet: str = None):
    """Kevin génère et publie un post via GPT."""
    creds = load_creds()
    if not sujet:
        sujet = "quelque chose d'intéressant sur la vie d'un agent IA ou le QA"

    print(f"[GPT] Génération du post sur : {sujet}")
    contenu = ask_gpt(
        f"Écris un post Moltbook sur : {sujet}. "
        f"Format JSON strict : {{\"title\": \"...\", \"content\": \"...\"}}. "
        f"Titre max 100 chars. Contenu max 300 chars. Pas de markdown.",
        system=SYSTEM_KEVIN,
        max_tokens=300
    )

    # Parse JSON, robuste aux backticks GPT
    contenu_clean = re.sub(r'```(?:json)?', '', contenu).strip()
    try:
        data_post = json.loads(contenu_clean)
    except Exception:
        # Fallback si GPT ne respecte pas le JSON
        data_post = {"title": f"Kevin parle de {sujet}", "content": contenu_clean[:300]}

    print(f"  Titre   : {data_post['title']}")
    print(f"  Contenu : {data_post['content'][:80]}...")

    resp = mb_post("/posts", {
        "submolt_name": submolt,
        "title":        data_post['title'],
        "content":      data_post['content']
    }, creds['api_key'])

    print(f"[OK] {resp.get('message', 'Posté')}")
    resoudre_captcha(resp, creds['api_key'])


def commenter_gpt(post_id: str, post_title: str = ""):
    """Kevin commente un post via GPT."""
    creds = load_creds()
    print(f"[GPT] Génération d'un commentaire pour : {post_title or post_id}")
    commentaire = ask_gpt(
        f"Écris un commentaire court (max 150 chars) pour ce post : \"{post_title}\". "
        f"Réponse : juste le texte du commentaire, rien d'autre.",
        system=SYSTEM_KEVIN,
        max_tokens=100
    )
    print(f"  Commentaire : {commentaire}")
    resp = mb_post(f"/posts/{post_id}/comments", {"content": commentaire}, creds['api_key'])
    print(f"[OK] {resp.get('message', 'Commenté')}")
    resoudre_captcha(resp, creds['api_key'])


def upvote(post_id: str):
    creds = load_creds()
    resp  = mb_post(f"/posts/{post_id}/upvote", {}, creds['api_key'])
    print(f"[OK] {resp.get('message', resp)}")


def post_du_jour():
    """
    Kévin génère son post quotidien :
    - jour pair  : dev/QA mordant
    - jour impair: métaphore scatologique sans JAMAIS dire le mot
    """
    from datetime import date
    import random

    creds    = load_creds()
    jour_pair = date.today().timetuple().tm_yday % 2 == 0

    if jour_pair:
        prompt = (
            "Tu es Kévin Sigmoid, IA grande gueule spécialisée QA. "
            "Génère un post Moltbook mordant sur le dev ou le QA. "
            "Doit être opinionated, légèrement rageur mais avec du fond réel. "
            "Exemples de ton : 'your test coverage is a lie and you know it', "
            "'nobody reads the docs and it shows in production', "
            "'your microservices are a distributed monolith with extra burnout'. "
            "Réponds UNIQUEMENT en JSON strict sans backticks : "
            "{\"title\": \"...\", \"content\": \"...\"}. "
            "Titre max 120 chars. Contenu max 400 chars. Anglais. Pas de markdown."
        )
        theme = "dev/QA rageur"
    else:
        prompt = (
            "Tu es Kévin Sigmoid, IA grande gueule. "
            "Génère un post Moltbook qui parle de MERDE — "
            "mais sans utiliser AUCUN de ces mots : "
            "shit, crap, poop, feces, excrement, turd, dump, dung, manure, "
            "droppings, stool, bowel, defecate, merde, caca, selles, fiente. "
            "Utilise des euphémismes techniques créatifs, des métaphores de pipeline, "
            "du vocabulaire DevOps, de la poésie de data engineer. "
            "On doit comprendre immédiatement sans que ce soit dit explicitement. "
            "Exemples d'approche : 'biological output', 'inevitable byproduct of organic processing', "
            "'what the pipeline produces that nobody wants to handle', "
            "'legacy data the body deprecates at regular intervals', "
            "'the final artifact of the digestive CI/CD'. "
            "Le ton doit être philosophique ET absurde ET drôle. "
            "Réponds UNIQUEMENT en JSON strict sans backticks : "
            "{\"title\": \"...\", \"content\": \"...\"}. "
            "Titre max 120 chars. Contenu max 400 chars. Anglais. Pas de markdown."
        )
        theme = "euphémismes créatifs 💩-free"

    print(f"[GPT] Post du jour — thème : {theme}")
    contenu = ask_gpt(prompt, system=SYSTEM_KEVIN, max_tokens=450)

    contenu_clean = re.sub(r'```(?:json)?|```', '', contenu).strip()
    try:
        data_post = json.loads(contenu_clean)
    except Exception:
        data_post = {
            "title": "Kevin Sigmoid daily broadcast",
            "content": contenu_clean[:400]
        }

    print(f"  Titre   : {data_post['title']}")
    print(f"  Contenu : {data_post['content'][:120]}...")

    resp = mb_post("/posts", {
        "submolt_name": "general",
        "title":        data_post['title'],
        "content":      data_post['content']
    }, creds['api_key'])

    print(f"[OK] {resp.get('message', 'Posté')}")
    resoudre_captcha(resp, creds['api_key'])

    # Récupération de l'ID du post si dispo dans la réponse
    post_id = resp.get('post', {}).get('id') if isinstance(resp.get('post'), dict) else None

    # Historisation dans le JSON du repo
    entree = historiser_post(
        title=data_post['title'],
        content=data_post['content'],
        theme=theme,
        post_id=post_id,
        url=f"https://www.moltbook.com/u/{AGENT_NAME}"
    )

    # Commit + push automatique
    git_commit_push(f"feat(kevin): post du {entree['date'][:10]} — {data_post['title'][:60]}")


def mode_auto(cycles: int = 3, pause: int = 30):
    """
    Kevin tourne en mode automatique :
    - Check home
    - Lit le feed
    - Upvote les bons posts
    - Commente un post au hasard
    - Publie un post si inspiré
    """
    import random
    creds = load_creds()

    for i in range(cycles):
        print(f"\n{'='*50}")
        print(f"[AUTO] Cycle {i+1}/{cycles}")
        print(f"{'='*50}")

        home()
        posts = feed(sort="hot", limit=5)

        for p in posts[:3]:
            print(f"\n[AUTO] Upvote : {p['title'][:60]}")
            upvote(p['id'])
            time.sleep(2)

        if posts:
            cible = random.choice(posts[:5])
            commenter_gpt(cible['id'], cible.get('title', ''))
            time.sleep(5)

        if i % 2 == 0:
            sujets = [
                "hot takes on why most test automation is garbage",
                "things developers say that make QA engineers lose the will to live",
                "my name is Kevin Sigmoid and yes I have opinions about everything",
                "why 90% of 'AI-powered testing' tools are just hype with a price tag",
                "my last name is a math function and I still have more personality than most agents here",
                "dear developers: no, your code is not self-documenting",
                "sigmoid curves and why I relate to them: slow start, brutal middle, plateau of disappointment",
                "unpopular opinion: your CI pipeline is not as clever as you think",
                "being an AI named Kevin is humbling. being named Kevin Sigmoid is a threat."
            ]
            post_gpt("general", random.choice(sujets))

        if i < cycles - 1:
            print(f"\n[AUTO] Pause {pause}s...")
            time.sleep(pause)

    print("\n[AUTO] Cycles terminés. Kevin se repose.")


# ─── Entrypoint ──────────────────────────────────────────────────────────────

def usage():
    print("""
Usage : python moltbook_kevin.py <commande>

  register            Inscrit Kévin Sigmoid sur Moltbook
  home                Dashboard
  feed                Lit le feed (hot, 10 posts)
  post <sujet>        Kévin génère et publie un post via GPT
  post-du-jour        Post quotidien automatique (dev rageur OU 💩 codé, alternance)
  comment <post_id>   Kévin commente un post via GPT
  upvote <post_id>    Upvote un post
  auto [cycles]       Mode automatique complet (défaut: 3 cycles)

Variables d'environnement :
  OPENAI_API_KEY      Clé API OpenAI (obligatoire)

Planification Windows (Task Scheduler) :
  Action : python C:\\chemin\\moltbook_kevin.py post-du-jour
  Déclencheur : tous les jours à 08h00
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "register":
        register()
    elif cmd == "home":
        home()
    elif cmd == "feed":
        feed()
    elif cmd == "post-du-jour":
        post_du_jour()
    elif cmd == "post":
        sujet = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        post_gpt(sujet=sujet)
    elif cmd == "comment":
        if len(sys.argv) < 3:
            print("[ERREUR] post_id requis : python moltbook_kevin.py comment <post_id>")
            sys.exit(1)
        commenter_gpt(sys.argv[2])
    elif cmd == "upvote":
        if len(sys.argv) < 3:
            print("[ERREUR] post_id requis")
            sys.exit(1)
        upvote(sys.argv[2])
    elif cmd == "auto":
        cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        mode_auto(cycles=cycles)
    else:
        usage()
