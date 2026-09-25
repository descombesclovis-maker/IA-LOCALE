import subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent

def wait_for_server(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen("http://127.0.0.1:3000/api/health", timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def main():
    bootstrap = ROOT / "local_app" / "bootstrap_windows.py"
    if bootstrap.exists():
        subprocess.run([sys.executable, str(bootstrap)], check=False)

    server = ROOT / "local_app" / "server.py"
    proc = subprocess.Popen([sys.executable, str(server)], cwd=str(ROOT))

    if not wait_for_server():
        proc.terminate()
        raise RuntimeError("LocalVisionAI n'a pas réussi à démarrer son moteur local.")

    try:
        import webview
    except ImportError:
        proc.terminate()
        raise RuntimeError("Le composant d'interface native pywebview est absent. Reconstruis LocalVisionAI.exe.")

    window = webview.create_window(
        "LocalVisionAI",
        "http://127.0.0.1:3000",
        width=1440,
        height=920,
        min_size=(1100, 700),
        resizable=True,
        background_color="#090909",
    )
    try:
        webview.start(debug=False)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()

if __name__ == "__main__":
    main()
