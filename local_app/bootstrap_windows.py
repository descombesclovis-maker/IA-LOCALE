import os, subprocess, urllib.request, json, zipfile, shutil, hashlib, sys
from pathlib import Path

DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "LocalVisionAI"
ENGINE = DATA / "ComfyUI"
LLAMA = DATA / "llama"
MODEL_DIR = DATA / "models"
COMFY_URL = "https://github.com/comfyanonymous/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z"
LLAMA_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
MODEL_URL = "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf?download=true"
MODEL_NAME = "Qwen3-8B-Q4_K_M.gguf"


def _download(url, dest, label):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 1024:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[LocalVisionAI] {label}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LocalVisionAI/1.0"})
        with urllib.request.urlopen(req, timeout=60) as src, open(tmp, "wb") as out:
            total = int(src.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if total:
                    pct = int(done * 100 / total)
                    print(f"  {pct}% ({done//(1024*1024)} / {total//(1024*1024)} MB)", end="\\r", flush=True)
        print()
        tmp.replace(dest)
    except Exception:
        try: tmp.unlink()
        except Exception: pass
        raise


def ensure_comfy():
    if (ENGINE / "run_nvidia_gpu.bat").exists() or (ENGINE / "main.py").exists():
        return True
    DATA.mkdir(parents=True, exist_ok=True)
    archive = DATA / "ComfyUI_windows_portable_nvidia.7z"
    _download(COMFY_URL, archive, "Téléchargement du moteur graphique ComfyUI…")
    target = DATA / "_extract_comfy"
    if target.exists(): shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    print("[LocalVisionAI] Extraction de ComfyUI…")
    r = subprocess.run(["tar", "-xf", str(archive), "-C", str(target)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("Impossible d'extraire ComfyUI automatiquement. Vérifie que Windows possède tar.exe.")
    candidates = list(target.rglob("run_nvidia_gpu.bat"))
    if not candidates:
        raise RuntimeError("Le paquet ComfyUI téléchargé ne contient pas le lanceur NVIDIA attendu.")
    source = candidates[0].parent
    if ENGINE.exists(): shutil.rmtree(ENGINE, ignore_errors=True)
    shutil.move(str(source), str(ENGINE))
    try: archive.unlink()
    except Exception: pass
    shutil.rmtree(target, ignore_errors=True)
    return True


def _llama_asset():
    req = urllib.request.Request(LLAMA_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "LocalVisionAI/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        release = json.loads(r.read().decode("utf-8"))
    assets = release.get("assets") or []
    # RTX/NVIDIA: CUDA 12.4 is the compatibility-first Windows build.
    matches = [a for a in assets if "win-cuda-12.4-x64.zip" in a.get("name","")]
    if not matches:
        raise RuntimeError("Aucun binaire llama.cpp Windows CUDA 12.4 x64 n'est disponible dans la dernière release.")
    return matches[0]


def ensure_llama():
    existing = list(LLAMA.rglob("llama-server.exe")) if LLAMA.exists() else []
    if existing:
        return True
    LLAMA.mkdir(parents=True, exist_ok=True)
    asset = _llama_asset()
    archive = DATA / asset["name"]
    _download(asset["browser_download_url"], archive, "Téléchargement de llama.cpp CUDA pour l'IA texte…")
    extract = DATA / "_extract_llama"
    if extract.exists(): shutil.rmtree(extract, ignore_errors=True)
    extract.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(extract)
    server = next(extract.rglob("llama-server.exe"), None)
    if not server:
        raise RuntimeError("llama.cpp a été téléchargé mais llama-server.exe est introuvable.")
    # Keep the complete DLL set next to llama-server.exe.
    for item in server.parent.iterdir():
        dest = LLAMA / item.name
        if item.is_dir(): shutil.copytree(item, dest, dirs_exist_ok=True)
        else: shutil.copy2(item, dest)
    shutil.rmtree(extract, ignore_errors=True)
    try: archive.unlink()
    except Exception: pass
    return True


def ensure_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model = MODEL_DIR / MODEL_NAME
    if model.exists() and model.stat().st_size > 4_500_000_000:
        return True
    _download(MODEL_URL, model, "Téléchargement du modèle conversationnel Qwen3 8B Q4… (~5 Go)")
    if model.stat().st_size < 4_500_000_000:
        raise RuntimeError("Le modèle GGUF téléchargé est incomplet.")
    return True


def run():
    DATA.mkdir(parents=True, exist_ok=True)
    ensure_comfy()
    ensure_llama()
    ensure_model()
    return True

if __name__ == "__main__":
    try:
        run()
        print("[LocalVisionAI] Installation locale prête.")
    except Exception as exc:
        print(f"[LocalVisionAI] ERREUR: {exc}")
        raise
