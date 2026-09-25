import json, os, subprocess, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

HOST = "127.0.0.1"
PORT = int(os.environ.get("LOCALVISIONAI_LLM_PORT", "8090"))
URL = f"http://{HOST}:{PORT}"
ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LocalVisionAI"
MODEL_DIR = DATA / "models"
ENGINE_DIR = DATA / "llama"
_proc = None

def _engine_candidates():
    roots = [ROOT / "llama", ROOT / "engine" / "llama", ENGINE_DIR]
    names = ["llama-server.exe", "llama.exe"]
    for root in roots:
        for name in names:
            p = root / name
            if p.exists():
                yield p

def find_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    preferred = os.environ.get("LOCALVISIONAI_LLM_MODEL")
    if preferred:
        p = Path(preferred).expanduser()
        if p.exists() and p.suffix.lower() == ".gguf":
            return p
    models = sorted(MODEL_DIR.rglob("*.gguf"), key=lambda p: p.stat().st_mtime, reverse=True)
    return models[0] if models else None

def online():
    try:
        req = Request(URL + "/v1/models", headers={"Accept": "application/json"})
        with urlopen(req, timeout=2) as r:
            return True, json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return False, str(e)

def ensure_server(timeout=45):
    global _proc
    ok, _ = online()
    if ok:
        return True
    engine = next(_engine_candidates(), None)
    model = find_model()
    if not engine or not model:
        return False
    try:
        ENGINE_DIR.mkdir(parents=True, exist_ok=True)
        args = [str(engine), "-m", str(model), "--host", HOST, "--port", str(PORT),
                "--alias", "localvision-model", "-c", "8192", "-ngl", "99"]
        _proc = subprocess.Popen(args, cwd=str(engine.parent),
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        ok, _ = online()
        if ok:
            return True
        time.sleep(0.5)
    return False

def status():
    ok, detail = online()
    model = find_model()
    engine = next(_engine_candidates(), None)
    return {
        "online": ok,
        "engine": str(engine) if engine else None,
        "model": str(model) if model else None,
        "model_name": model.name if model else None,
        "model_dir": str(MODEL_DIR),
        "url": URL,
        "detail": detail if not ok else None,
    }

def chat(messages, settings=None):
    settings = settings or {}
    if not ensure_server():
        raise RuntimeError(
            "IA conversationnelle locale non configurée. "
            f"Ajoute un moteur llama-server.exe dans {ENGINE_DIR} et un modèle GGUF dans {MODEL_DIR}."
        )
    payload = {
        "model": "localvision-model",
        "messages": messages,
        "stream": False,
        "temperature": float(settings.get("temperature", 0.7)),
        "top_p": float(settings.get("top_p", 0.9)),
        "max_tokens": int(settings.get("max_tokens", 1024)),
    }
    req = Request(URL + "/v1/chat/completions",
                  data=json.dumps(payload).encode("utf-8"),
                  headers={"Content-Type": "application/json"},
                  method="POST")
    with urlopen(req, timeout=300) as r:
        data = json.loads(r.read().decode("utf-8"))
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Le moteur local n'a renvoyé aucune réponse.")
    return choices[0].get("message", {}).get("content", "")
