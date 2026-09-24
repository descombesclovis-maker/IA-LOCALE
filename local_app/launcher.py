import subprocess, sys, time, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    bootstrap = ROOT / "local_app" / "bootstrap_windows.py"
    if bootstrap.exists():
        subprocess.run([sys.executable, str(bootstrap)], check=False)
    server = ROOT / "local_app" / "server.py"
    proc = subprocess.Popen([sys.executable, str(server)], cwd=str(ROOT))
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:3000")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()
