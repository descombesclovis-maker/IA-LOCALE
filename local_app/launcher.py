import os, sys, time, threading
from pathlib import Path
from urllib.request import urlopen
import json

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "LocalVisionAI"
os.environ["LOCALVISIONAI_DATA"] = str(DATA)


def wait_for_server(timeout=900):
    deadline=time.time()+timeout
    while time.time()<deadline:
        try:
            with urlopen("http://127.0.0.1:3000/api/health",timeout=3) as r:
                if r.status==200:
                    data=json.loads(r.read().decode("utf-8"))
                    if data.get("online") and (data.get("llm") or {}).get("online"):
                        return True
        except Exception:
            pass
        time.sleep(1)
    return False


def main():
    # First-run setup is performed before the UI appears. In a frozen build,
    # bootstrap.py is bundled and imported from PyInstaller's temporary folder.
    from local_app import bootstrap_windows
    bootstrap_windows.run()

    import local_app.server as server
    server_thread=threading.Thread(target=server.main,daemon=True)
    server_thread.start()
    if not wait_for_server():
        raise RuntimeError("Les moteurs locaux n'ont pas pu démarrer. Consulte le journal LocalVisionAI dans AppData\\Local\\LocalVisionAI.")

    try:
        import webview
    except ImportError as exc:
        raise RuntimeError("pywebview est absent du paquet LocalVisionAI.") from exc

    window=webview.create_window("LocalVisionAI","http://127.0.0.1:3000",width=1440,height=920,
                                  min_size=(1100,700),resizable=True,background_color="#090909")
    webview.start(debug=False)

if __name__=="__main__": main()
