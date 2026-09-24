import os, subprocess, urllib.request
from pathlib import Path

DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "LocalVisionAI"
ENGINE = DATA / "ComfyUI"
URL = "https://github.com/comfyanonymous/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z"

def run():
    if (ENGINE / "run_nvidia_gpu.bat").exists() or (ENGINE / "main.py").exists():
        return True
    DATA.mkdir(parents=True, exist_ok=True)
    archive = DATA / "ComfyUI_windows_portable_nvidia.7z"
    print("Premier démarrage : téléchargement du moteur graphique local...")
    urllib.request.urlretrieve(URL, archive)
    print("Extraction du moteur local...")
    target = DATA / "_extract"
    target.mkdir(exist_ok=True)
    r = subprocess.run(["tar", "-xf", str(archive), "-C", str(target)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("Impossible d'extraire ComfyUI automatiquement. Installe 7-Zip puis relance LocalVisionAI.")
    candidates = list(target.rglob("run_nvidia_gpu.bat"))
    if not candidates:
        raise RuntimeError("Le paquet ComfyUI téléchargé est incomplet.")
    import shutil
    source = candidates[0].parent
    if ENGINE.exists():
        shutil.rmtree(ENGINE, ignore_errors=True)
    source.rename(ENGINE)
    try:
        archive.unlink()
    except Exception:
        pass
    shutil.rmtree(target, ignore_errors=True)
    return True

if __name__ == "__main__":
    run()
